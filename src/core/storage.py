import logging
import uuid
from pathlib import PurePath

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from src.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_TZ_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}
MAX_TZ_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


class S3Storage:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
        self.bucket = settings.S3_BUCKET_NAME

    def ensure_bucket(self) -> None:
        try:
            try:
                self.client.head_bucket(Bucket=self.bucket)
            except ClientError:
                self.client.create_bucket(Bucket=self.bucket)
        except Exception as exc:
            logger.warning(
                "S3 unavailable at startup, file uploads will fail until it is running: %s",
                exc,
            )

    def upload_hackathon_tz(self, hackathon_id: int, file: UploadFile) -> str:
        extension = PurePath(file.filename or "").suffix.lower()
        if extension not in ALLOWED_TZ_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_TZ_EXTENSIONS))}"
            )

        content = file.file.read()
        if len(content) > MAX_TZ_FILE_SIZE:
            raise ValueError(f"File too large. Max size: {MAX_TZ_FILE_SIZE // (1024 * 1024)} MB")

        safe_name = PurePath(file.filename or "tz").name
        key = f"hackathons/{hackathon_id}/tz/{uuid.uuid4().hex}_{safe_name}"

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=file.content_type or "application/octet-stream",
        )

        return f"{settings.S3_PUBLIC_BASE_URL.rstrip('/')}/{key}"


s3_storage = S3Storage()
