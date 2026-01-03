"""
MinIO Service - Main Service Class.

Composes all layer mixins into a unified MinIO service for data lake operations.
"""

import logging
from typing import Any

from minio import Minio

from cortex.services.minio.bronze import BronzeLayerMixin
from cortex.services.minio.config import MinIOSettings, get_minio_settings
from cortex.services.minio.gold import GoldLayerMixin
from cortex.services.minio.query import QueryMixin
from cortex.services.minio.silver import SilverLayerMixin

logger = logging.getLogger(__name__)


class MinIOService(
    BronzeLayerMixin,
    SilverLayerMixin,
    GoldLayerMixin,
    QueryMixin,
):
    """
    MinIO Data Lake Service (Medallion Architecture).

    Manages Bronze (landing), Silver (source of truth), and Gold (tabular data) layers.

    - Bronze: Temporary landing zone for raw uploads
    - Silver: Source of truth for document metadata (categories as tags)
    - Gold: Processed/transformed tabular data (business-ready)

    Example:
        from cortex.services.minio import get_minio_service

        minio = get_minio_service()
        bronze_key = minio.upload_to_bronze(file_path, filename)
        silver_key = minio.copy_to_silver(bronze_key, ...)
        gold_key = minio.save_to_gold(document_id, data_type, df)
    """

    def __init__(self, settings: MinIOSettings | None = None) -> None:
        """
        Initialize MinIO service with connection and buckets.

        Args:
            settings: MinIO settings. If None, loads from environment.
        """
        self.settings = settings or get_minio_settings()
        self.endpoint = self.settings.minio_endpoint
        self.access_key = self.settings.minio_access_key
        self.secret_key = self.settings.minio_secret_key
        self.bronze_bucket = self.settings.minio_bronze_bucket
        self.silver_bucket = self.settings.minio_silver_bucket
        self.gold_bucket = self.settings.minio_gold_bucket

        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.settings.minio_secure,
        )

        self._ensure_buckets()

    def _ensure_buckets(self) -> None:
        """Create buckets if they don't exist."""
        try:
            if not self.client.bucket_exists(self.bronze_bucket):
                self.client.make_bucket(self.bronze_bucket)
                logger.info(f"Created Bronze bucket: {self.bronze_bucket}")

            if not self.client.bucket_exists(self.silver_bucket):
                self.client.make_bucket(self.silver_bucket)
                logger.info(f"Created Silver bucket: {self.silver_bucket}")

            if not self.client.bucket_exists(self.gold_bucket):
                self.client.make_bucket(self.gold_bucket)
                logger.info(f"Created Gold bucket: {self.gold_bucket}")
        except Exception as e:
            logger.error(f"Error ensuring buckets: {e}")
            raise

    def health_check(self) -> dict[str, Any]:
        """
        Check MinIO connection and bucket status.

        Returns:
            Health status dict with connection and bucket info.
        """
        try:
            bronze_exists = self.client.bucket_exists(self.bronze_bucket)
            silver_exists = self.client.bucket_exists(self.silver_bucket)
            gold_exists = self.client.bucket_exists(self.gold_bucket)

            return {
                "status": (
                    "healthy"
                    if (bronze_exists and silver_exists and gold_exists)
                    else "degraded"
                ),
                "endpoint": self.endpoint,
                "bronze_bucket": {"name": self.bronze_bucket, "exists": bronze_exists},
                "silver_bucket": {"name": self.silver_bucket, "exists": silver_exists},
                "gold_bucket": {"name": self.gold_bucket, "exists": gold_exists},
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "endpoint": self.endpoint,
            }


# Singleton instance for reuse
_minio_service: MinIOService | None = None


def get_minio_service() -> MinIOService:
    """
    Get or create MinIO service singleton instance.

    Returns:
        MinIOService instance.
    """
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service
