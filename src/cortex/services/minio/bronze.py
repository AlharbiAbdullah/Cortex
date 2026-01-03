"""
Bronze Layer Operations.

Landing zone for raw uploads (temporary storage).
Files are copied to Silver after processing and then deleted from Bronze.
"""

import logging
import os
import uuid
from io import BytesIO
from typing import BinaryIO

from minio import Minio

logger = logging.getLogger(__name__)


class BronzeLayerMixin:
    """
    Mixin providing Bronze layer operations.

    Bronze layer is the landing zone for raw uploads.
    Files are temporary and should be moved to Silver after processing.
    """

    client: Minio
    bronze_bucket: str

    def upload_to_bronze(
        self,
        file_path: str,
        filename: str,
        document_id: str | None = None,
    ) -> str:
        """
        Upload raw file to Bronze layer (landing zone).

        Args:
            file_path: Local path to the file.
            filename: Original filename.
            document_id: Stable document identifier (UUID). Generated if omitted.

        Returns:
            bronze_key: Key in Bronze bucket (e.g., uploads/<uuid>.pdf).
        """
        if not document_id:
            document_id = uuid.uuid4().hex
        ext = os.path.splitext(filename)[1].lower()
        bronze_key = f"uploads/{document_id}{ext}"

        try:
            self.client.fput_object(self.bronze_bucket, bronze_key, file_path)
            logger.info(f"Uploaded to Bronze: {bronze_key}")
            return bronze_key
        except Exception as e:
            logger.error(f"Failed to upload to Bronze: {e}")
            raise

    def upload_bytes_to_bronze(
        self,
        data: bytes,
        filename: str,
        document_id: str | None = None,
    ) -> str:
        """
        Upload bytes directly to Bronze layer.

        Args:
            data: File content as bytes.
            filename: Original filename.
            document_id: Stable document identifier (UUID). Generated if omitted.

        Returns:
            bronze_key: Key in Bronze bucket.
        """
        if not document_id:
            document_id = uuid.uuid4().hex
        ext = os.path.splitext(filename)[1].lower()
        bronze_key = f"uploads/{document_id}{ext}"

        try:
            data_stream = BytesIO(data)
            self.client.put_object(
                self.bronze_bucket,
                bronze_key,
                data_stream,
                length=len(data),
            )
            logger.info(f"Uploaded bytes to Bronze: {bronze_key}")
            return bronze_key
        except Exception as e:
            logger.error(f"Failed to upload bytes to Bronze: {e}")
            raise

    def upload_stream_to_bronze(
        self,
        data_stream: BinaryIO,
        length: int,
        filename: str,
        document_id: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """
        Upload a stream directly to Bronze layer.

        Args:
            data_stream: File-like object opened in binary mode.
            length: Total bytes to upload.
            filename: Original filename.
            document_id: Stable document identifier (UUID). Generated if omitted.
            content_type: Optional MIME type.

        Returns:
            bronze_key: Key in Bronze bucket.
        """
        if not document_id:
            document_id = uuid.uuid4().hex
        ext = os.path.splitext(filename)[1].lower()
        bronze_key = f"uploads/{document_id}{ext}"

        if length is None or int(length) <= 0:
            raise ValueError("Invalid upload length")

        try:
            self.client.put_object(
                self.bronze_bucket,
                bronze_key,
                data_stream,
                length=int(length),
                content_type=content_type,
            )
            logger.info(f"Uploaded stream to Bronze: {bronze_key}")
            return bronze_key
        except Exception as e:
            logger.error(f"Failed to upload stream to Bronze: {e}")
            raise

    def get_file_from_bronze(self, bronze_key: str) -> bytes:
        """
        Download file content from Bronze layer.

        Args:
            bronze_key: Key in Bronze bucket.

        Returns:
            File content as bytes.
        """
        try:
            response = self.client.get_object(self.bronze_bucket, bronze_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            logger.error(f"Failed to get file from Bronze: {e}")
            raise

    def get_bronze_file_to_path(self, bronze_key: str, local_path: str) -> None:
        """
        Download Bronze file to local path.

        Args:
            bronze_key: Key in Bronze bucket.
            local_path: Local filesystem path to save file.
        """
        try:
            self.client.fget_object(self.bronze_bucket, bronze_key, local_path)
            logger.info(f"Downloaded Bronze file to: {local_path}")
        except Exception as e:
            logger.error(f"Failed to download Bronze file: {e}")
            raise

    def delete_from_bronze(self, bronze_key: str) -> None:
        """
        Delete file from Bronze layer (cleanup after Silver copy).

        Args:
            bronze_key: Key in Bronze bucket.
        """
        try:
            self.client.remove_object(self.bronze_bucket, bronze_key)
            logger.info(f"Deleted from Bronze: {bronze_key}")
        except Exception as e:
            logger.error(f"Failed to delete from Bronze: {e}")
            # Don't raise - cleanup failure shouldn't break the flow
