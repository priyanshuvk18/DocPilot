"""
Object storage service with S3/MinIO and local filesystem fallback.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

LOCAL_STORAGE_DIR = Path("data/storage")


class StorageService:
    def __init__(self) -> None:
        self.endpoint = settings.storage_endpoint_url
        self.bucket = settings.storage_bucket_name
        self._s3_client = None

        # Ensure local storage directory exists
        LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

        if not ("localhost" in self.endpoint and "minioadmin" in settings.storage_access_key_id.get_secret_value()):
            try:
                import boto3
                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint,
                    aws_access_key_id=settings.storage_access_key_id.get_secret_value(),
                    aws_secret_access_key=settings.storage_secret_access_key.get_secret_value(),
                    region_name=settings.storage_region,
                )
            except Exception as e:
                logger.warning("Could not initialize S3 client, using local storage", error=str(e))

    def save_file(self, filename: str, content: bytes) -> str:
        """Save file bytes and return storage path."""
        storage_path = f"{filename}"
        if self._s3_client:
            try:
                self._s3_client.put_object(
                    Bucket=self.bucket,
                    Key=storage_path,
                    Body=content,
                )
                return storage_path
            except Exception as e:
                logger.warning("S3 put_object failed, saving locally", error=str(e))

        local_path = LOCAL_STORAGE_DIR / storage_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
        return str(local_path)

    def read_file(self, storage_path: str) -> bytes:
        """Read file bytes from storage."""
        if self._s3_client:
            try:
                resp = self._s3_client.get_object(Bucket=self.bucket, Key=storage_path)
                return resp["Body"].read()
            except Exception as e:
                logger.warning("S3 get_object failed, checking local storage", error=str(e))

        local_path = Path(storage_path)
        if not local_path.is_absolute():
            local_path = LOCAL_STORAGE_DIR / storage_path
        if local_path.exists():
            return local_path.read_bytes()

        return b""


storage_service = StorageService()
