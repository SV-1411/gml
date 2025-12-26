# Complete Fix: Storage Upload Route Not Found

## CRITICAL: You Must Restart the Server

The route exists in the code but **WILL NOT WORK** until you restart the backend server.

## Step-by-Step Fix

### 1. STOP the Backend Server
- Find your terminal running `uvicorn`
- Press `Ctrl+C`
- Wait until it says "Shutting down" or stops

### 2. RESTART the Server
```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. CHECK Server Output
Look for these messages in the server output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Storage router registered at /api/v1/storage
INFO:     Storage routes registered: ['/upload', '/url/{key}']
INFO:     All routes configured successfully
INFO:     Registered routers: agents, health, memory, ollama, storage
INFO:     Application startup complete.
```

**If you see "Storage router registered" → Route is loaded!**
**If you DON'T see it → There's an import error (check logs)**

### 4. VERIFY Route is Available

Open in browser:
```
http://localhost:8000/api/docs
```

**Look for "storage" section** (should be at the bottom)
- Click on it
- You should see:
  - `POST /api/v1/storage/upload`
  - `GET /api/v1/storage/url/{key}`

### 5. TEST the Route

```bash
# Create a test file
echo "test content" > /tmp/test.txt

# Upload it
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/tmp/test.txt" \
  -F "bucket=uploads"
```

**Success Response:**
```json
{
  "url": "http://localhost:9000/uploads/abc123-test.txt",
  "key": "abc123-test.txt",
  "bucket": "uploads",
  "size": 12,
  "filename": "test.txt",
  "content_type": "text/plain"
}
```

## Why It's Not Working

**The route IS in the code:**
- ✅ File: `src/gml/api/routes/storage.py` (exists)
- ✅ Route: `POST /upload` (defined)
- ✅ Router prefix: `/storage` (set)
- ✅ Exported in `__init__.py` (yes)
- ✅ Imported in `main.py` (yes)
- ✅ Registered with prefix `/api/v1` (yes)

**The problem:** The running server process doesn't know about it yet.

**The solution:** RESTART the server so it reloads the code.

## Troubleshooting

### Issue: Server starts but route still not found

**Check server logs for:**
1. "Storage router registered" message
2. Any import errors
3. Any exception messages

**If you see import errors:**
```bash
# Install missing dependencies
pip install minio

# Restart server again
```

### Issue: Route appears in docs but returns 404

**Check:**
1. URL path is correct: `/api/v1/storage/upload`
2. Method is POST (not GET)
3. Content-Type is `multipart/form-data` for file uploads

### Issue: Import Error

If you see:
```
ImportError: cannot import name 'storage_router'
```

**Fix:**
1. Check `src/gml/api/routes/__init__.py` exports `storage_router`
2. Check `src/gml/api/routes/storage.py` exists
3. Check for syntax errors in storage.py

## Quick Verification Script

After restarting, run this to verify:

```bash
# Check if route is in API docs
curl -s http://localhost:8000/api/openapi.json | grep -i "storage/upload"

# Should output something like:
# "/api/v1/storage/upload"
```

## Important Notes

1. **`--reload` flag helps but sometimes you need FULL restart**
2. **Clear Python cache if issues persist:**
   ```bash
   find src -name "*.pyc" -delete
   find src -type d -name __pycache__ -exec rm -r {} +
   ```
3. **MinIO is optional** - route works without it (uses placeholder URLs)

## Final Checklist

- [ ] Server stopped completely
- [ ] Server restarted with uvicorn
- [ ] See "Storage router registered" in logs
- [ ] Route appears in http://localhost:8000/api/docs
- [ ] curl test works
- [ ] Frontend can upload files

If all checked → Route is working!

