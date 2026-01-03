"""
Silver Layer Operations.

Final destination for documents with category tags (permanent storage).
Silver layer IS the source of truth for document metadata.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any

from minio import Minio
from minio.commonconfig import CopySource, Tags

from cortex.services.minio.config import VALID_TAG_KEYS
from cortex.services.minio.helpers import (
    extract_document_id_from_key,
    format_categories_with_scores,
    format_confidence_tag,
    normalize_tags_dict,
    sanitize_tag_value,
)

logger = logging.getLogger(__name__)


class SilverLayerMixin:
    """
    Mixin providing Silver layer operations.

    Silver layer is the source of truth for documents.
    Categories are stored as MinIO object tags (mutable).
    """

    client: Minio
    bronze_bucket: str
    silver_bucket: str

    def copy_to_silver(
        self,
        bronze_key: str,
        document_id: str,
        filename: str,
        file_type: str,
        primary_category: str,
        categories: list[str],
        confidence: float,
        reasoning: str = "",
        status: str = "processed",
        feed_the_brain: int = 1,
        feed_the_graph: int = 0,
        tableur: int = 0,
        category_scores: dict[str, float] | None = None,
        silver_filename: str | None = None,
    ) -> str:
        """
        Copy file from Bronze to Silver with category tags.

        Args:
            bronze_key: Source key in Bronze bucket.
            document_id: Stable document identifier (UUID).
            filename: Original filename.
            file_type: File type (pdf, docx, excel, txt).
            primary_category: Main category.
            categories: All categories (including primary).
            confidence: Classification confidence score.
            reasoning: LLM reasoning for classification.
            status: Processing status.
            feed_the_brain: Include in Q/A service (1=include, 0=exclude).
            feed_the_graph: Route to Neo4j graph database (1=route, 0=skip).
            tableur: Process tabular data to Gold (1=process, 0=skip).
            category_scores: Optional per-category confidence scores.
            silver_filename: Optional custom filename for Silver layer.

        Returns:
            silver_key: Key in Silver bucket.
        """
        ext = os.path.splitext(filename)[1].lower()
        if silver_filename:
            silver_key = f"docs/{silver_filename}{ext}"
        else:
            silver_key = f"docs/{document_id}{ext}"

        copied = False
        try:
            self.client.copy_object(
                self.silver_bucket,
                silver_key,
                CopySource(self.bronze_bucket, bronze_key),
            )
            copied = True
            logger.info(f"Copied to Silver: {silver_key}")

            self._set_silver_tags(
                silver_key,
                document_id,
                filename,
                file_type,
                primary_category,
                categories,
                confidence,
                reasoning,
                status,
                feed_the_brain,
                feed_the_graph,
                tableur,
                category_scores,
            )

            self.delete_from_bronze(bronze_key)
            return silver_key

        except Exception as e:
            if copied:
                try:
                    self.client.remove_object(self.silver_bucket, silver_key)
                    logger.warning(f"Rolled back Silver object: {silver_key}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to rollback {silver_key}: {cleanup_err}")
            logger.error(f"Failed to copy to Silver: {e}")
            raise

    def _set_silver_tags(
        self,
        silver_key: str,
        document_id: str,
        filename: str,
        file_type: str,
        primary_category: str,
        categories: list[str],
        confidence: float,
        reasoning: str = "",
        status: str = "processed",
        feed_the_brain: int = 1,
        feed_the_graph: int = 0,
        tableur: int = 0,
        category_scores: dict[str, float] | None = None,
    ) -> None:
        """Set all metadata tags on Silver object."""
        try:
            tags = Tags.new_object_tags()
            tags["document_id"] = sanitize_tag_value(document_id, 128)
            tags["file_type"] = sanitize_tag_value(file_type, 32)

            if category_scores:
                categories_tag = format_categories_with_scores(categories, category_scores)
            else:
                categories_tag = "+".join(categories)

            tags["categories"] = sanitize_tag_value(categories_tag, 256)
            tags["confidence"] = sanitize_tag_value(format_confidence_tag(confidence), 32)
            tags["upload_date"] = sanitize_tag_value(
                datetime.now(timezone.utc).isoformat(), 64
            )
            tags["status"] = sanitize_tag_value(status, 32)
            tags["feed_the_brain"] = str(int(feed_the_brain)) if feed_the_brain in (0, 1) else "1"
            tags["feed_the_graph"] = str(int(feed_the_graph)) if feed_the_graph in (0, 1) else "0"
            tags["tableur"] = str(int(tableur)) if tableur in (0, 1) else "0"

            if reasoning:
                tags["reasoning"] = sanitize_tag_value(reasoning, 200)

            self.client.set_object_tags(self.silver_bucket, silver_key, tags)
            logger.info(f"Set tags on {silver_key}: categories={categories_tag}")

        except Exception as e:
            logger.error(f"Failed to set tags: {e}")
            raise

    def update_tags(
        self,
        silver_key: str,
        primary_category: str,
        categories: list[str],
        confidence: float,
        reasoning: str = "",
        feed_the_brain: int | None = None,
        feed_the_graph: int | None = None,
        tableur: int | None = None,
        category_scores: dict[str, float] | None = None,
    ) -> None:
        """
        Update category tags on existing Silver object (for re-learning).

        Args:
            silver_key: Key in Silver bucket.
            primary_category: New primary category.
            categories: New category list.
            confidence: New confidence score.
            reasoning: New LLM reasoning.
            feed_the_brain: Optional update for Q/A inclusion.
            feed_the_graph: Optional update for graph routing.
            tableur: Optional update for tabular processing.
            category_scores: Optional per-category confidence scores.
        """
        try:
            existing_tags = self.get_tags(silver_key)

            tags = Tags.new_object_tags()
            tags["document_id"] = sanitize_tag_value(
                existing_tags.get("document_id", extract_document_id_from_key(silver_key)),
                128,
            )
            tags["file_type"] = sanitize_tag_value(
                existing_tags.get("file_type", "unknown"), 32
            )
            tags["upload_date"] = sanitize_tag_value(
                existing_tags.get("upload_date", datetime.now(timezone.utc).isoformat()),
                64,
            )

            if category_scores:
                categories_tag = format_categories_with_scores(categories, category_scores)
            else:
                categories_tag = "+".join(categories)

            tags["categories"] = sanitize_tag_value(categories_tag, 256)
            tags["confidence"] = sanitize_tag_value(format_confidence_tag(confidence), 32)
            tags["status"] = "relearned"
            tags["relearn_date"] = sanitize_tag_value(
                datetime.now(timezone.utc).isoformat(), 64
            )

            if feed_the_brain is not None:
                tags["feed_the_brain"] = str(int(feed_the_brain)) if feed_the_brain in (0, 1) else "1"
            else:
                tags["feed_the_brain"] = existing_tags.get("feed_the_brain", "1")

            if feed_the_graph is not None:
                tags["feed_the_graph"] = str(int(feed_the_graph)) if feed_the_graph in (0, 1) else "0"
            else:
                tags["feed_the_graph"] = existing_tags.get("feed_the_graph", "0")

            if tableur is not None:
                tags["tableur"] = str(int(tableur)) if tableur in (0, 1) else "0"
            else:
                tags["tableur"] = existing_tags.get("tableur", "0")

            if reasoning:
                tags["reasoning"] = sanitize_tag_value(reasoning, 200)

            self.client.set_object_tags(self.silver_bucket, silver_key, tags)
            logger.info(f"Updated tags on {silver_key}: categories={categories_tag}")

        except Exception as e:
            logger.error(f"Failed to update tags: {e}")
            raise

    def update_feed_the_brain(self, silver_key: str, feed_the_brain: int) -> bool:
        """Update only the feed_the_brain tag."""
        if feed_the_brain not in (0, 1):
            raise ValueError("feed_the_brain must be 0 or 1")

        try:
            existing_tags = self.get_tags(silver_key)
            if not existing_tags:
                logger.error(f"No existing tags found for {silver_key}")
                return False

            tags = Tags.new_object_tags()
            for key, value in existing_tags.items():
                if key and value and key in VALID_TAG_KEYS:
                    tags[key] = sanitize_tag_value(value, 256)

            tags["feed_the_brain"] = str(feed_the_brain)
            self.client.set_object_tags(self.silver_bucket, silver_key, tags)
            logger.info(f"Updated feed_the_brain on {silver_key}: {feed_the_brain}")
            return True

        except Exception as e:
            logger.error(f"Failed to update feed_the_brain: {e}")
            return False

    def get_tags(self, silver_key: str) -> dict[str, str]:
        """Get current tags from Silver object."""
        try:
            tags = self.client.get_object_tags(self.silver_bucket, silver_key)
            return normalize_tags_dict(tags)
        except Exception as e:
            logger.error(f"Failed to get tags: {e}")
            return {}

    def get_file_from_silver(self, silver_key: str) -> bytes:
        """Download file content from Silver layer."""
        try:
            response = self.client.get_object(self.silver_bucket, silver_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            logger.error(f"Failed to get file from Silver: {e}")
            raise

    def get_silver_file_to_path(self, silver_key: str, local_path: str) -> None:
        """
        Download Silver file to local path.

        Args:
            silver_key: Key in Silver bucket.
            local_path: Local filesystem path to save file.
        """
        try:
            self.client.fget_object(self.silver_bucket, silver_key, local_path)
            logger.info(f"Downloaded Silver file to: {local_path}")
        except Exception as e:
            logger.error(f"Failed to download Silver file: {e}")
            raise

    def delete_from_silver(self, silver_key: str) -> None:
        """Delete file from Silver layer."""
        try:
            self.client.remove_object(self.silver_bucket, silver_key)
            logger.info(f"Deleted from Silver: {silver_key}")
        except Exception as e:
            logger.error(f"Failed to delete from Silver: {e}")
            raise

    def list_silver_objects(self, prefix: str = "docs/") -> list[dict[str, Any]]:
        """List raw objects in Silver layer."""
        try:
            objects = []
            for obj in self.client.list_objects(self.silver_bucket, prefix=prefix):
                objects.append({
                    "key": obj.object_name,
                    "size": obj.size,
                    "last_modified": (
                        obj.last_modified.isoformat() if obj.last_modified else None
                    ),
                })
            return objects
        except Exception as e:
            logger.error(f"Failed to list Silver objects: {e}")
            return []
