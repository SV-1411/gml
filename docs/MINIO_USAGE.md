# MinIO Usage Guide

## Overview

MinIO is an S3-compatible object storage service used in this project for file storage. This guide explains how to use MinIO with the GML Infrastructure project.

## Setup

### 1. Start MinIO Service

```bash
# Start MinIO using Docker Compose
docker-compose -f docker-compose.dev.yml up -d minio

# Or start all services
docker-compose -f docker-compose.dev.yml up -d
```

### 2. Access MinIO Console

- **Console URL:** http://localhost:9001
- **API URL:** http://localhost:9000
- **Username:** `minioadmin`
- **Password:** `minioadmin`

### 3. Default Buckets

The following buckets are automatically created:
- **uploads** - For user file uploads (public download enabled)
- **backups** - For backup files
- **models** - For AI model files

## Using MinIO in the Project

### Method 1: Via Frontend UI

1. **Upload File from Memory Form:**
   - Go to Memories page
   - Click "Create Memory"
   - Scroll to "Upload File (Optional)" section
   - Select a file
   - File will be uploaded to MinIO automatically
   - Storage URL will be displayed

2. **View Storage URLs:**
   - Storage URLs are shown in memory search results
   - Click on the URL to download the file
   - Use "Copy" button to copy URL to clipboard

### Method 2: Via API

#### Upload File

```bash
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/path/to/your/file.pdf" \
  -F "bucket=uploads"
```

**Response:**
```json
{
  "url": "http://localhost:9000/uploads/abc123def456-file.pdf",
  "key": "abc123def456-file.pdf",
  "bucket": "uploads",
  "size": 1024,
  "filename": "file.pdf",
  "content_type": "application/pdf"
}
```

#### Get File URL

```bash
curl http://localhost:8000/api/v1/storage/url/abc123def456-file.pdf?bucket=uploads
```

**Response:**
```json
{
  "url": "http://localhost:9000/uploads/abc123def456-file.pdf",
  "key": "abc123def456-file.pdf",
  "bucket": "uploads"
}
```

### Method 3: Using MinIO Console (Web UI)

1. **Login:**
   - Navigate to http://localhost:9001
   - Login with `minioadmin` / `minioadmin`

2. **Browse Buckets:**
   - Click on a bucket (e.g., "uploads")
   - View files stored in the bucket

3. **Upload File:**
   - Click "Upload" button
   - Select file(s) to upload
   - Files are stored in the bucket

4. **Download File:**
   - Click on a file to download
   - Or use the URL format: `http://localhost:9000/{bucket}/{filename}`

### Method 4: Using Python (MinIO Client)

```python
from minio import Minio
from minio.error import S3Error

# Initialize MinIO client
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False  # Set to True for HTTPS
)

# Upload file
try:
    minio_client.fput_object(
        "uploads",  # bucket name
        "my-file.pdf",  # object name
        "/path/to/local/file.pdf"  # file path
    )
    print("File uploaded successfully")
except S3Error as e:
    print(f"Error uploading file: {e}")

# Download file
try:
    minio_client.fget_object(
        "uploads",
        "my-file.pdf",
        "/path/to/download/file.pdf"
    )
    print("File downloaded successfully")
except S3Error as e:
    print(f"Error downloading file: {e}")

# List files in bucket
try:
    objects = minio_client.list_objects("uploads")
    for obj in objects:
        print(f"File: {obj.object_name}, Size: {obj.size}")
except S3Error as e:
    print(f"Error listing files: {e}")
```

## Storage URLs

### URL Format

```
http://localhost:9000/{bucket}/{file_key}
```

**Examples:**
- `http://localhost:9000/uploads/document.pdf`
- `http://localhost:9000/backups/backup-2024-01-15.tar.gz`
- `http://localhost:9000/models/model-v1.0.bin`

### Accessing Files

**Public Access (uploads bucket):**
- Files in the `uploads` bucket have public download access
- Direct URL access: `http://localhost:9000/uploads/filename.pdf`

**Private Access:**
- Other buckets require authentication
- Use MinIO client or API with credentials

## Integration in Memory Storage

When you upload a file through the Memory form:

1. **File Upload Process:**
   ```
   Frontend → POST /api/v1/storage/upload
              ↓
   Backend → MinIO Storage
              ↓
   Returns: Storage URL
              ↓
   Frontend → Stores URL in memory content
   ```

2. **Memory Content Structure:**
   ```json
   {
     "text": "File description",
     "storage_url": "http://localhost:9000/uploads/abc123-file.pdf",
     "file_key": "abc123-file.pdf",
     "file_size": 1024,
     "file_type": "application/pdf"
   }
   ```

3. **Search Results:**
   - Memory search results show storage URLs
   - URLs are clickable and can be copied
   - Files can be downloaded directly

## Configuration

### Environment Variables

Add to `.env` file:

```bash
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_UPLOADS=uploads
```

### Change Credentials (Production)

Edit `docker-compose.dev.yml`:

```yaml
environment:
  MINIO_ROOT_USER: your-secure-username
  MINIO_ROOT_PASSWORD: your-secure-password
```

Then restart:
```bash
docker-compose -f docker-compose.dev.yml restart minio
```

## Troubleshooting

### MinIO Not Starting

**Problem:** MinIO container fails to start

**Solution:**
```bash
# Check logs
docker logs gml-minio

# Check if ports are already in use
lsof -i :9000
lsof -i :9001

# Restart container
docker-compose -f docker-compose.dev.yml restart minio
```

### Cannot Access Console

**Problem:** Cannot access http://localhost:9001

**Solutions:**
1. Verify MinIO is running: `docker ps | grep minio`
2. Check firewall settings
3. Try accessing from container: `docker exec -it gml-minio curl http://localhost:9000/minio/health/live`

### File Upload Fails

**Problem:** File upload returns error

**Solutions:**
1. Check MinIO is running and healthy
2. Verify bucket exists (check console)
3. Check file size limits
4. Verify network connectivity between backend and MinIO

### Files Not Accessible via URL

**Problem:** Storage URLs return 404

**Solutions:**
1. Verify bucket policy allows public access (for uploads bucket)
2. Check file key is correct
3. Verify MinIO is accessible at the URL
4. Check bucket name matches

## Best Practices

1. **Bucket Organization:**
   - Use `uploads` for user-uploaded files
   - Use `backups` for system backups
   - Use `models` for AI model files
   - Create additional buckets for specific use cases

2. **File Naming:**
   - Use unique file keys (UUID-based)
   - Include file extension
   - Avoid special characters

3. **Access Control:**
   - Keep sensitive files in private buckets
   - Use presigned URLs for temporary access
   - Implement proper authentication

4. **Cleanup:**
   - Regularly clean up old files
   - Implement retention policies
   - Monitor storage usage

## API Endpoints

- `POST /api/v1/storage/upload` - Upload file
- `GET /api/v1/storage/url/{key}` - Get file URL

For full API documentation, visit: http://localhost:8000/api/docs

