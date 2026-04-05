"""
Storage API Routes

Provides file storage endpoints using Supabase Storage.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status

from src.gml.api.dependencies import get_db
from src.gml.services.supabase_client import SupabaseDB, get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storage", tags=["storage"])


@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file",
)
async def upload_file(
    file: UploadFile = File(...),
    bucket: str = Query("uploads", description="Storage bucket name"),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Upload a file to Supabase Storage."""
    try:
        client = await get_supabase_client()
        
        # Read file content
        content = await file.read()
        
        # Upload to Supabase Storage
        path = f"{file.filename}"
        result = await client.storage.from_(bucket).upload(path, content)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]["message"],
            )
        
        # Get public URL
        public_url = client.storage.from_(bucket).get_public_url(path)
        
        logger.info(f"File uploaded: {file.filename} to {bucket}")
        
        return {
            "filename": file.filename,
            "bucket": bucket,
            "path": path,
            "url": public_url,
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )


@router.get(
    "/list",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List files",
)
async def list_files(
    bucket: str = Query("uploads"),
    prefix: Optional[str] = Query(None),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """List files in storage bucket."""
    try:
        client = await get_supabase_client()
        
        result = await client.storage.from_(bucket).list(prefix or "")
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]["message"],
            )
        
        return {
            "bucket": bucket,
            "files": result,
            "total": len(result),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list files",
        )


@router.delete(
    "/delete",
    status_code=status.HTTP_200_OK,
    summary="Delete file",
)
async def delete_file(
    path: str = Query(..., description="File path in bucket"),
    bucket: str = Query("uploads"),
    db: SupabaseDB = Depends(get_db),
) -> dict:
    """Delete a file from storage."""
    try:
        client = await get_supabase_client()
        
        result = await client.storage.from_(bucket).remove([path])
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]["message"],
            )
        
        logger.info(f"File deleted: {path} from {bucket}")
        
        return {
            "path": path,
            "bucket": bucket,
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        )


__all__ = ["router"]
