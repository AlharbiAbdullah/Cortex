"""MinIO service module for data lake operations (Bronze/Silver/Gold)."""

from cortex.services.minio.service import MinIOService, get_minio_service

__all__ = ["MinIOService", "get_minio_service"]
