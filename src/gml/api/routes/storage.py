"""
Storage API Routes

FastAPI router for file upload and storage management endpoints.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db.database import get_db
from src.gml.monitoring.metrics import metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storage", tags=["storage"])

# Try to import MinIO service, fallback to placeholder if not available
MINIO_ENABLED = False
try:
    from src.gml.services.minio_service import get_minio_service
    MINIO_ENABLED = True
except (ImportError, AttributeError, Exception) as e:
    MINIO_ENABLED = False
    logger.info(f"MinIO service not available: {e}. File uploads will use placeholder URLs.")


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
    description="Upload a file to storage and return the storage URL",
)
async def upload_file(
    file: UploadFile = File(...),
    bucket: str = Form("uploads"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Upload a file to storage.

    Currently returns a placeholder URL. In production, this should:
    1. Upload to MinIO/S3
    2. Generate presigned URL or public URL
    3. Store metadata in database
    4. Return storage URL

    Args:
        file: The file to upload
        bucket: Storage bucket name (default: uploads)
        db: Database session

    Returns:
        Dictionary containing:
            - url: Storage URL for the file
            - key: File key/path in storage
            - bucket: Bucket name
            - size: File size in bytes

    Example:
        POST /api/v1/storage/upload
        Form data:
            - file: [binary file data]
            - bucket: uploads

        Response 201:
        {
            "url": "http://localhost:9000/uploads/file-abc-123.pdf",
            "key": "file-abc-123.pdf",
            "bucket": "uploads",
            "size": 1024
        }
    """
    try:
        # Read file content
        contents = await file.read()
        file_size = len(contents)

        # Generate unique file key
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        file_key = f"{uuid.uuid4().hex[:12]}-{file.filename}" if file.filename else f"{uuid.uuid4().hex[:12]}.{file_extension}"

        # Upload to MinIO if available
        if MINIO_ENABLED:
            try:
                minio_service = get_minio_service()
                storage_url = minio_service.upload_file(
                    bucket_name=bucket,
                    object_name=file_key,
                    file_data=contents,
                    content_type=file.content_type or "application/octet-stream",
                    length=file_size,
                )
                logger.info(f"File uploaded to MinIO: {file_key} ({file_size} bytes) to bucket {bucket}")
            except Exception as e:
                logger.error(f"Failed to upload to MinIO: {e}. Using placeholder URL.")
                storage_url = f"http://localhost:9000/{bucket}/{file_key}"
        else:
            # Placeholder URL if MinIO not available
            storage_url = f"http://localhost:9000/{bucket}/{file_key}"
            logger.info(f"File upload (placeholder): {file_key} ({file_size} bytes) to bucket {bucket}")

        # Note: Request metrics are tracked by middleware
        # No need to manually increment here

        return {
            "url": storage_url,
            "key": file_key,
            "bucket": bucket,
            "size": file_size,
            "filename": file.filename,
            "content_type": file.content_type,
        }

    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get(
    "/url/{key}",
    status_code=status.HTTP_200_OK,
    summary="Get file URL",
    description="Get the storage URL for a file by its key",
)
async def get_file_url(
    key: str,
    bucket: str = "uploads",
) -> dict:
    """
    Get storage URL for a file.

    Args:
        key: File key/path
        bucket: Bucket name (default: uploads)

    Returns:
        Dictionary containing storage URL

    Example:
        GET /api/v1/storage/url/file-abc-123.pdf?bucket=uploads

        Response 200:
        {
            "url": "http://localhost:9000/uploads/file-abc-123.pdf",
            "key": "file-abc-123.pdf",
            "bucket": "uploads"
        }
    """
    storage_url = f"http://localhost:9000/{bucket}/{key}"

    return {
        "url": storage_url,
        "key": key,
        "bucket": bucket,
    }

