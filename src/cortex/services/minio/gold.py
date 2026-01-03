"""
Gold Layer Operations.

Processed/transformed tabular data (permanent, business-ready data).
Stores extracted structured data in Parquet format.
"""

import logging
import os
import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Iterator

import pandas as pd
from minio import Minio
from minio.commonconfig import Tags

from cortex.services.minio.helpers import (
    extract_document_id_from_key,
    normalize_tags_dict,
    sanitize_tag_value,
)

logger = logging.getLogger(__name__)


class GoldLayerMixin:
    """
    Mixin providing Gold layer operations.

    Gold layer stores processed/transformed tabular data in Parquet format.
    """

    client: Minio
    gold_bucket: str

    def save_to_gold(
        self,
        document_id: str,
        data_type: str,
        df: pd.DataFrame,
        source_silver_key: str | None = None,
        filename: str | None = None,
    ) -> str:
        """
        Save DataFrame to Gold layer as Parquet.

        Args:
            document_id: Source document identifier.
            data_type: Type of extracted data ('names', 'transactions', 'tables').
            df: pandas DataFrame to save.
            source_silver_key: Optional Silver key reference.
            filename: Optional original filename for reference.

        Returns:
            gold_key: Key in Gold bucket.
        """
        if filename:
            base_filename = os.path.splitext(filename)[0]
            safe_filename = re.sub(r"[^\w\-_.]", "_", base_filename)
            gold_key = f"{data_type}/{safe_filename}.parquet"
        else:
            gold_key = f"{data_type}/{document_id}.parquet"

        record_count = len(df)

        try:
            df = df.copy()
            df["_document_id"] = document_id
            df["_data_type"] = data_type
            df["_source_silver_key"] = source_silver_key
            df["_source_filename"] = filename
            df["_created_at"] = datetime.now(timezone.utc).isoformat()

            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, engine="pyarrow", index=False)
            parquet_buffer.seek(0)
            parquet_bytes = parquet_buffer.getvalue()
            parquet_buffer.seek(0)

            self.client.put_object(
                self.gold_bucket,
                gold_key,
                parquet_buffer,
                length=len(parquet_bytes),
                content_type="application/vnd.apache.parquet",
            )

            tags = Tags.new_object_tags()
            tags["document_id"] = sanitize_tag_value(document_id, 128)
            tags["data_type"] = sanitize_tag_value(data_type, 64)
            tags["record_count"] = str(record_count)
            tags["created_at"] = sanitize_tag_value(
                datetime.now(timezone.utc).isoformat(), 64
            )
            if source_silver_key:
                tags["source_silver_key"] = sanitize_tag_value(source_silver_key, 256)
            if filename:
                tags["source_filename"] = sanitize_tag_value(filename, 128)

            self.client.set_object_tags(self.gold_bucket, gold_key, tags)
            logger.info(f"Saved {record_count} records to Gold: {gold_key}")
            return gold_key

        except Exception as e:
            logger.error(f"Failed to save to Gold: {e}")
            raise

    def save_to_gold_chunked(
        self,
        document_id: str,
        data_type: str,
        chunk_iterator: Iterator[pd.DataFrame],
        source_silver_key: str | None = None,
        filename: str | None = None,
    ) -> str:
        """
        Save large DataFrame to Gold layer by concatenating chunks.

        Args:
            document_id: Source document identifier.
            data_type: Type of extracted data.
            chunk_iterator: Iterator that yields DataFrame chunks.
            source_silver_key: Optional Silver key reference.
            filename: Optional original filename.

        Returns:
            gold_key: Key in Gold bucket.
        """
        if filename:
            base_filename = os.path.splitext(filename)[0]
            safe_filename = re.sub(r"[^\w\-_.]", "_", base_filename)
            gold_key = f"{data_type}/{safe_filename}.parquet"
        else:
            gold_key = f"{data_type}/{document_id}.parquet"

        created_at = datetime.now(timezone.utc).isoformat()

        try:
            df = pd.concat(chunk_iterator, ignore_index=True)
            record_count = len(df)

            df["_document_id"] = document_id
            df["_data_type"] = data_type
            df["_source_silver_key"] = source_silver_key
            df["_source_filename"] = filename
            df["_created_at"] = created_at

            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, engine="pyarrow", index=False)
            parquet_buffer.seek(0)
            parquet_bytes = parquet_buffer.getvalue()
            parquet_buffer.seek(0)

            self.client.put_object(
                self.gold_bucket,
                gold_key,
                parquet_buffer,
                length=len(parquet_bytes),
                content_type="application/vnd.apache.parquet",
            )

            tags = Tags.new_object_tags()
            tags["document_id"] = sanitize_tag_value(document_id, 128)
            tags["data_type"] = sanitize_tag_value(data_type, 64)
            tags["record_count"] = str(record_count)
            tags["created_at"] = sanitize_tag_value(created_at, 64)
            if source_silver_key:
                tags["source_silver_key"] = sanitize_tag_value(source_silver_key, 256)
            if filename:
                tags["source_filename"] = sanitize_tag_value(filename, 128)

            self.client.set_object_tags(self.gold_bucket, gold_key, tags)
            logger.info(f"Saved {record_count} records to Gold (chunked): {gold_key}")
            return gold_key

        except Exception as e:
            logger.error(f"Failed to save to Gold (chunked): {e}")
            raise

    def get_from_gold(self, gold_key: str) -> dict[str, Any] | None:
        """
        Get processed data from Gold layer.

        Args:
            gold_key: Key in Gold bucket.

        Returns:
            Gold record dict or None if not found.
        """
        try:
            response = self.client.get_object(self.gold_bucket, gold_key)
            data = response.read()
            response.close()
            response.release_conn()

            parquet_buffer = BytesIO(data)
            df = pd.read_parquet(parquet_buffer, engine="pyarrow")

            document_id = (
                df["_document_id"].iloc[0]
                if "_document_id" in df.columns and len(df) > 0
                else None
            )
            data_type = (
                df["_data_type"].iloc[0]
                if "_data_type" in df.columns and len(df) > 0
                else None
            )
            source_silver_key = (
                df["_source_silver_key"].iloc[0]
                if "_source_silver_key" in df.columns and len(df) > 0
                else None
            )
            source_filename = (
                df["_source_filename"].iloc[0]
                if "_source_filename" in df.columns and len(df) > 0
                else None
            )
            created_at = (
                df["_created_at"].iloc[0]
                if "_created_at" in df.columns and len(df) > 0
                else None
            )

            data_columns = [col for col in df.columns if not col.startswith("_")]
            data_df = df[data_columns]

            return {
                "document_id": document_id,
                "data_type": data_type,
                "source_silver_key": source_silver_key,
                "source_filename": source_filename,
                "record_count": len(df),
                "created_at": created_at,
                "data": data_df.to_dict(orient="records"),
            }
        except Exception as e:
            logger.error(f"Failed to get from Gold: {e}")
            return None

    def list_gold_data(
        self,
        data_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List all tabular data in Gold layer.

        Args:
            data_type: Optional filter by data type.
            limit: Maximum number of results.

        Returns:
            List of Gold data metadata dicts.
        """
        try:
            prefix = f"{data_type}/" if data_type else ""
            gold_items = []
            count = 0

            for obj in self.client.list_objects(
                self.gold_bucket, prefix=prefix, recursive=True
            ):
                if count >= limit:
                    break

                tags = {}
                try:
                    raw_tags = self.client.get_object_tags(
                        self.gold_bucket, obj.object_name
                    )
                    tags = normalize_tags_dict(raw_tags)
                except Exception:
                    pass

                key_parts = obj.object_name.split("/")
                extracted_data_type = key_parts[0] if len(key_parts) > 1 else "unknown"

                gold_items.append({
                    "gold_key": obj.object_name,
                    "document_id": tags.get(
                        "document_id",
                        extract_document_id_from_key(obj.object_name),
                    ),
                    "data_type": tags.get("data_type", extracted_data_type),
                    "record_count": (
                        int(tags.get("record_count", 0))
                        if tags.get("record_count")
                        else 0
                    ),
                    "source_silver_key": tags.get("source_silver_key"),
                    "source_filename": tags.get("source_filename"),
                    "created_at": tags.get("created_at"),
                    "size": obj.size,
                    "last_modified": (
                        obj.last_modified.isoformat() if obj.last_modified else None
                    ),
                })
                count += 1

            gold_items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
            return gold_items

        except Exception as e:
            logger.error(f"Failed to list Gold data: {e}")
            return []

    def delete_from_gold(self, gold_key: str) -> None:
        """Delete data from Gold layer."""
        try:
            self.client.remove_object(self.gold_bucket, gold_key)
            logger.info(f"Deleted from Gold: {gold_key}")
        except Exception as e:
            logger.error(f"Failed to delete from Gold: {e}")
            raise

    def get_gold_stats(self) -> dict[str, Any]:
        """Get statistics about Gold layer data."""
        try:
            all_gold = self.list_gold_data(limit=10000)

            by_type: dict[str, dict[str, Any]] = {}
            total_records = 0

            for item in all_gold:
                data_type = item.get("data_type", "unknown")
                if data_type not in by_type:
                    by_type[data_type] = {"count": 0, "total_records": 0}
                by_type[data_type]["count"] += 1
                by_type[data_type]["total_records"] += item.get("record_count", 0)
                total_records += item.get("record_count", 0)

            return {
                "total_files": len(all_gold),
                "total_records": total_records,
                "by_data_type": by_type,
            }
        except Exception as e:
            logger.error(f"Failed to get Gold stats: {e}")
            return {"total_files": 0, "total_records": 0, "by_data_type": {}}
