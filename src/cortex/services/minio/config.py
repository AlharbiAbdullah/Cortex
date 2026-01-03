"""MinIO service configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class MinIOSettings(BaseSettings):
    """MinIO connection and bucket configuration."""

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_secure: bool = False

    # Bucket names (Medallion Architecture)
    minio_bronze_bucket: str = "bronze"
    minio_silver_bucket: str = "silver"
    minio_gold_bucket: str = "gold"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_minio_settings() -> MinIOSettings:
    """Get cached MinIO settings."""
    return MinIOSettings()


# S3/MinIO tag values are restrictive (AWS-compatible)
TAG_ALLOWED_EXTRA_CHARS = set(" +-=_:/.@")

# Valid tag keys (max 10 for S3/MinIO)
VALID_TAG_KEYS = {
    "document_id",
    "file_type",
    "categories",
    "confidence",
    "upload_date",
    "status",
    "feed_the_brain",
    "feed_the_graph",
    "tableur",
    "relearn_date",
    "reasoning",
}
