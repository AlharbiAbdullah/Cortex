"""
Background job manager for upload processing.

Handles upload processing in background threads with job tracking.
Supports both in-memory and Redis-backed persistent storage.
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import lru_cache, partial
from threading import Lock
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class JobManagerSettings(BaseSettings):
    """Job manager configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    use_redis_jobs: bool = True
    upload_job_workers: int = 1


@lru_cache()
def get_job_manager_settings() -> JobManagerSettings:
    """Get cached job manager settings instance."""
    return JobManagerSettings()


def _utc_now_iso() -> str:
    """Return current UTC time as ISO format string."""
    return datetime.now(timezone.utc).isoformat()


class UploadJobManager:
    """
    Manages background upload processing jobs.

    Supports two storage backends:
    - Redis (default): Persistent storage that survives restarts
    - In-memory: Fallback when Redis is unavailable or disabled

    The storage backend is selected based on the use_redis_jobs setting.
    """

    def __init__(self, max_workers: int = 1):
        """
        Initialize the job manager.

        Args:
            max_workers: Maximum number of concurrent worker threads.
        """
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max(1, max_workers))
        self._settings = get_job_manager_settings()

        # In-memory fallback storage
        self._jobs: dict[str, dict[str, Any]] = {}
        self._jobs_lock = Lock()

        # Redis store (lazy loaded)
        self._redis_store: Any | None = None

        # Background-only DocumentService instance (avoid cross-thread use)
        self._bg_document_service: Any | None = None
        self._bg_document_service_lock = Lock()

        logger.info(
            f"JobManager initialized (Redis: {self._settings.use_redis_jobs}, "
            f"workers: {max_workers})"
        )

    def _get_redis_store(self):
        """Get or create Redis job store."""
        if self._redis_store is None and self._settings.use_redis_jobs:
            try:
                from cortex.jobs.redis_store import get_job_store

                self._redis_store = get_job_store()
            except ImportError:
                logger.warning("Redis store not available, using in-memory fallback")
        return self._redis_store

    def _get_bg_document_service(self):
        """Get or create background DocumentService instance."""
        from cortex.services.document_service import DocumentService

        with self._bg_document_service_lock:
            if self._bg_document_service is None:
                self._bg_document_service = DocumentService()
            return self._bg_document_service

    def set_job(self, job_id: str, **updates: Any) -> None:
        """
        Update job status.

        Uses Redis if available, falls back to in-memory storage.

        Args:
            job_id: Job identifier.
            **updates: Fields to update.
        """
        redis_store = self._get_redis_store()
        if redis_store:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(redis_store.update_job(job_id, **updates))
                loop.close()
                return
            except Exception as e:
                logger.warning(f"Redis update failed, using fallback: {e}")

        # Fallback to in-memory
        with self._jobs_lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(updates)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job status.

        Args:
            job_id: Job identifier.

        Returns:
            Job data dict or None if not found.
        """
        redis_store = self._get_redis_store()
        if redis_store:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                job = loop.run_until_complete(redis_store.get_job(job_id))
                loop.close()
                if job:
                    return job
            except Exception as e:
                logger.warning(f"Redis read failed, checking fallback: {e}")

        # Fallback to in-memory
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        List recent jobs sorted by creation time.

        Args:
            limit: Maximum number of jobs to return.

        Returns:
            List of job data dicts.
        """
        redis_store = self._get_redis_store()
        if redis_store:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                jobs = loop.run_until_complete(redis_store.list_jobs(limit))
                loop.close()
                return jobs
            except Exception as e:
                logger.warning(f"Redis list failed, using fallback: {e}")

        # Fallback to in-memory
        with self._jobs_lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.get("created_at") or "", reverse=True)
        return jobs[:limit]

    def create_job(
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
            "created_at": _utc_now_iso(),
            "filename": filename,
            "document_id": document_id,
            "bronze_key": bronze_key,
        }

        redis_store = self._get_redis_store()
        if redis_store:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                job = loop.run_until_complete(
                    redis_store.create_job(job_id, filename, document_id, bronze_key)
                )
                loop.close()
                return job
            except Exception as e:
                logger.warning(f"Redis create failed, using fallback: {e}")

        # Fallback to in-memory
        with self._jobs_lock:
            self._jobs[job_id] = job
        return job

    async def process_upload_async(
        self,
        job_id: str,
        bronze_key: str,
        filename: str,
        document_id: str,
    ) -> None:
        """
        Process upload in background (async).

        Args:
            job_id: Job identifier.
            bronze_key: MinIO bronze bucket key.
            filename: Original filename.
            document_id: Document identifier.
        """
        from cortex.agents.smart_router import SmartRouterGraph

        self.set_job(job_id, status="processing", started_at=_utc_now_iso())

        try:
            # Use a dedicated router instance for the background worker
            router = SmartRouterGraph()

            result = await router.run(
                bronze_key=bronze_key,
                filename=filename,
                document_id=document_id,
            )

            if result.get("status") == "error" or not result.get("silver_key"):
                if "raw_content" in result:
                    del result["raw_content"]
                self.set_job(
                    job_id,
                    status="error",
                    error=result.get("error") or "Smart routing failed",
                    finished_at=_utc_now_iso(),
                    result=result,
                )
                return

            # Trigger ChromaDB Sync for RAG
            if result.get("silver_key"):
                try:
                    bg_doc_service = self._get_bg_document_service()
                    silver_key = result["silver_key"]
                    chroma_result = await bg_doc_service.ingest_from_silver(
                        doc_key=silver_key,
                        silver_key=silver_key,
                        filename=filename,
                        file_type=result.get("file_type", "unknown"),
                        categories=result.get("all_categories", []),
                    )
                    result["chroma_sync"] = "success"
                    if "chunk_count" in chroma_result:
                        result["chunk_count"] = chroma_result.get("chunk_count", 0)
                except Exception as e:
                    logger.error(f"ChromaDB sync failed (job_id={job_id}): {e}")
                    result["chroma_sync"] = f"failed: {str(e)}"

                    # Fallback to raw_content if Silver read fails
                    if result.get("raw_content") and result.get("silver_key"):
                        try:
                            bg_doc_service = self._get_bg_document_service()
                            silver_key = result["silver_key"]
                            chroma_result = await bg_doc_service.ingest_text(
                                doc_key=silver_key,
                                filename=filename,
                                text=result["raw_content"],
                                file_type=result.get("file_type", "unknown"),
                            )
                            result["chroma_sync"] = "success (fallback)"
                            if chroma_result.get("chunk_count"):
                                result["chunk_count"] = chroma_result["chunk_count"]
                        except Exception as e2:
                            logger.error(
                                f"ChromaDB fallback sync also failed "
                                f"(job_id={job_id}): {e2}"
                            )

            # Remove raw_content from stored result (too large)
            if "raw_content" in result:
                del result["raw_content"]

            self.set_job(
                job_id,
                status="completed",
                finished_at=_utc_now_iso(),
                result=result,
            )
        except Exception as e:
            logger.error(
                f"Upload background job failed (job_id={job_id}): {e}",
                exc_info=True,
            )
            self.set_job(
                job_id,
                status="error",
                error=str(e),
                finished_at=_utc_now_iso(),
            )

    def _run_upload_job(
        self,
        job_id: str,
        bronze_key: str,
        filename: str,
        document_id: str,
    ) -> None:
        """Sync wrapper to run async upload processing."""
        try:
            asyncio.run(
                self.process_upload_async(job_id, bronze_key, filename, document_id)
            )
        except Exception as e:
            logger.error(
                f"Upload job runner crashed (job_id={job_id}): {e}",
                exc_info=True,
            )
            self.set_job(
                job_id,
                status="error",
                error=str(e),
                finished_at=_utc_now_iso(),
            )

    def submit_job(
        self,
        job_id: str,
        bronze_key: str,
        filename: str,
        document_id: str,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """
        Submit a job for background processing.

        Args:
            job_id: Job identifier.
            bronze_key: MinIO bronze bucket key.
            filename: Original filename.
            document_id: Document identifier.
            loop: Event loop to use for executor.
        """
        loop.run_in_executor(
            self._executor,
            partial(self._run_upload_job, job_id, bronze_key, filename, document_id),
        )


# Singleton instance
_job_manager: UploadJobManager | None = None


def get_job_manager() -> UploadJobManager:
    """Get or create the singleton job manager."""
    global _job_manager
    if _job_manager is None:
        settings = get_job_manager_settings()
        _job_manager = UploadJobManager(max_workers=settings.upload_job_workers)
    return _job_manager
