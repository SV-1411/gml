"""
MinIO Service

Service for interacting with MinIO object storage.
Provides file upload, download, and URL generation functionality.
"""

import logging
from typing import Optional
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    logger.warning("MinIO client not installed. Install with: pip install minio")


class MinIOService:
    """
    Service for MinIO operations.
    
    Handles file uploads, downloads, and URL generation for MinIO storage.
    """
    
    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure: bool = False,
    ):
        """
        Initialize MinIO service.
        
        Args:
            endpoint: MinIO server endpoint (host:port)
            access_key: MinIO access key
            secret_key: MinIO secret key
            secure: Use HTTPS (default: False for local development)
        """
        if not MINIO_AVAILABLE:
            raise ImportError(
                "MinIO client not available. Install with: pip install minio"
            )
        
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        
        try:
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            logger.info(f"MinIO client initialized for {endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: bytes,
        content_type: Optional[str] = "application/octet-stream",
        length: Optional[int] = None,
    ) -> str:
        """
        Upload a file to MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object (file key)
            file_data: File content as bytes
            content_type: MIME type of the file
            length: Length of file data (if None, uses len(file_data))
        
        Returns:
            Storage URL for the uploaded file
        
        Raises:
            S3Error: If upload fails
            Exception: For other errors
        """
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            
            # Upload file
            data = BytesIO(file_data)
            length = length or len(file_data)
            
            self.client.put_object(
                bucket_name,
                object_name,
                data,
                length=length,
                content_type=content_type,
            )
            
            # Generate URL
            url = self._generate_url(bucket_name, object_name)
            
            logger.info(f"Uploaded file to MinIO: {bucket_name}/{object_name}")
            
            return url
            
        except S3Error as e:
            logger.error(f"MinIO S3 error uploading {object_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to upload file to MinIO: {e}")
            raise
    
    def get_file_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: Optional[int] = None,
    ) -> str:
        """
        Get URL for a file in MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object (file key)
            expires: Expiration time in seconds for presigned URL (None for public URL)
        
        Returns:
            URL to access the file
        """
        if expires:
            # Generate presigned URL
            try:
                url = self.client.presigned_get_object(
                    bucket_name, object_name, expires=expires
                )
                return url
            except S3Error as e:
                logger.error(f"Failed to generate presigned URL: {e}")
                raise
        else:
            # Generate public URL
            return self._generate_url(bucket_name, object_name)
    
    def _generate_url(self, bucket_name: str, object_name: str) -> str:
        """
        Generate public URL for a file.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
        
        Returns:
            Public URL
        """
        protocol = "https" if self.secure else "http"
        return f"{protocol}://{self.endpoint}/{bucket_name}/{object_name}"
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Check if a file exists in MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
        
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
        except Exception:
            return False
    
    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete a file from MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Name of the object
        
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Deleted file from MinIO: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False


# Singleton instance
_minio_service: Optional[MinIOService] = None


def get_minio_service() -> MinIOService:
    """
    Get MinIO service singleton instance.
    
    Returns:
        MinIOService instance
    """
    global _minio_service
    
    if _minio_service is None:
        # Load from environment or use defaults
        import os
        _minio_service = MinIOService(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
        )
    
    return _minio_service

