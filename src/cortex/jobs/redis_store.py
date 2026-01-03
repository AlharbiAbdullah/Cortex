"""
Redis-based job storage for background processing.

Provides persistent job storage that survives application restarts.
Falls back to in-memory storage if Redis is unavailable.
"""

import json
import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://redis:6379/0"
    job_ttl_seconds: int = 86400  # 24 hours default
    job_key_prefix: str = "cortex:job:"


@lru_cache()
def get_redis_settings() -> RedisSettings:
    """Get cached Redis settings instance."""
    return RedisSettings()


class RedisJobStore:
    """
    Redis-based job storage with automatic TTL and fallback.

    Stores job data in Redis with configurable TTL. Falls back to in-memory
    storage if Redis connection fails.

    Attributes:
        redis_url: Redis connection URL.
        ttl_seconds: Time-to-live for job data.
        _redis: Redis client (async).
        _fallback_store: In-memory dict used when Redis is unavailable.
        _redis_available: Whether Redis connection is working.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        ttl_seconds: int | None = None,
    ):
        """
        Initialize Redis job store.

        Args:
            redis_url: Redis connection URL. Defaults to settings.
            ttl_seconds: Time-to-live for job data in seconds. Defaults to settings.
        """
        settings = get_redis_settings()
        self.redis_url = redis_url or settings.redis_url
        self.ttl_seconds = ttl_seconds or settings.job_ttl_seconds
        self._key_prefix = settings.job_key_prefix
        self._redis = None
        self._redis_available = False
        self._fallback_store: dict[str, dict[str, Any]] = {}

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis

                self._redis = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self._redis.ping()
                self._redis_available = True
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed, using fallback: {e}")
                self._redis_available = False
                self._redis = None

        return self._redis

    def _job_key(self, job_id: str) -> str:
        """Generate Redis key for a job."""
        return f"{self._key_prefix}{job_id}"

    async def create_job(
        self,
        job_id: str,
        filename: str,
        document_id: str,
        bronze_key: str,
    ) -> dict[str, Any]:
        """
        Create a new job entry.

        Args:
            job_id: Unique job identifier.
            filename: Original filename.
            document_id: Document identifier.
            bronze_key: MinIO bronze bucket key.

        Returns:
            Job data dict.
        """
        job = {
            "job_id": job_id,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "filename": filename,
            "document_id": document_id,
            "bronze_key": bronze_key,
        }

        redis_client = await self._get_redis()
        if redis_client and self._redis_available:
            try:
                await redis_client.setex(
                    self._job_key(job_id),
                    self.ttl_seconds,
                    json.dumps(job),
                )
            except Exception as e:
                logger.warning(f"Redis write failed, using fallback: {e}")
                self._redis_available = False
                self._fallback_store[job_id] = job
        else:
            self._fallback_store[job_id] = job

        return job

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job data by ID.

        Args:
            job_id: Job identifier.

        Returns:
            Job data dict or None if not found.
        """
        redis_client = await self._get_redis()
        if redis_client and self._redis_available:
            try:
                data = await redis_client.get(self._job_key(job_id))
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis read failed, checking fallback: {e}")
                self._redis_available = False

        return self._fallback_store.get(job_id)

    async def update_job(self, job_id: str, **updates: Any) -> bool:
        """
        Update job data.

        Args:
            job_id: Job identifier.
            **updates: Fields to update.

        Returns:
            True if job was updated, False if not found.
        """
        job = await self.get_job(job_id)
        if not job:
            return False

        job.update(updates)

        redis_client = await self._get_redis()
        if redis_client and self._redis_available:
            try:
                # Get remaining TTL and preserve it
                ttl = await redis_client.ttl(self._job_key(job_id))
                if ttl < 0:
                    ttl = self.ttl_seconds

                await redis_client.setex(
                    self._job_key(job_id),
                    ttl,
                    json.dumps(job),
                )
                return True
            except Exception as e:
                logger.warning(f"Redis update failed, using fallback: {e}")
                self._redis_available = False

        self._fallback_store[job_id] = job
        return True

    async def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        List recent jobs sorted by creation time.

        Args:
            limit: Maximum number of jobs to return.

        Returns:
            List of job data dicts.
        """
        jobs = []

        redis_client = await self._get_redis()
        if redis_client and self._redis_available:
            try:
                # Scan for job keys
                cursor = 0
                keys = []
                while True:
                    cursor, batch = await redis_client.scan(
                        cursor, match=f"{self._key_prefix}*", count=100
                    )
                    keys.extend(batch)
                    if cursor == 0:
                        break

                # Get job data in batch
                if keys:
                    pipeline = redis_client.pipeline()
                    for key in keys[: limit * 2]:  # Get extra to filter
                        pipeline.get(key)
                    results = await pipeline.execute()

                    for data in results:
                        if data:
                            try:
                                jobs.append(json.loads(data))
                            except (json.JSONDecodeError, TypeError):
                                continue

            except Exception as e:
                logger.warning(f"Redis list failed, using fallback: {e}")
                self._redis_available = False
                jobs = list(self._fallback_store.values())
        else:
            jobs = list(self._fallback_store.values())

        # Sort by creation time (newest first) and limit
        jobs.sort(key=lambda j: j.get("created_at") or "", reverse=True)
        return jobs[:limit]

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: Job identifier.

        Returns:
            True if job was deleted.
        """
        redis_client = await self._get_redis()
        if redis_client and self._redis_available:
            try:
                await redis_client.delete(self._job_key(job_id))
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        if job_id in self._fallback_store:
            del self._fallback_store[job_id]

        return True

    async def health_check(self) -> dict[str, Any]:
        """
        Check Redis connection health.

        Returns:
            Health status dict.
        """
        redis_client = await self._get_redis()
        if redis_client and self._redis_available:
            try:
                await redis_client.ping()
                return {
                    "status": "healthy",
                    "backend": "redis",
                    "url": self.redis_url.split("@")[-1],  # Hide credentials
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "backend": "fallback",
                    "error": str(e),
                }

        return {
            "status": "degraded",
            "backend": "fallback",
            "message": "Redis unavailable, using in-memory storage",
        }

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton instance
_job_store: RedisJobStore | None = None


def get_job_store() -> RedisJobStore:
    """Get or create the singleton job store."""
    global _job_store
    if _job_store is None:
        _job_store = RedisJobStore()
    return _job_store
