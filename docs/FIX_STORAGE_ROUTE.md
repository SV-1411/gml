# Fix: Storage Upload Endpoint Not Found

## Problem
Error: `Endpoint /api/v1/storage/upload not found`

## Solution: Restart Backend Server

The storage route was just added to the codebase. You need to **restart your backend server** for it to be available.

### Step 1: Stop Current Server

If your backend server is running:
- Find the terminal where `uvicorn` is running
- Press `Ctrl+C` to stop it

### Step 2: Restart Backend Server

```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

Wait for the message:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Verify Route is Available

**Option 1: Check API Documentation**
```bash
# Open in browser
open http://localhost:8000/api/docs

# Look for "storage" section
# You should see:
# - POST /api/v1/storage/upload
# - GET /api/v1/storage/url/{key}
```

**Option 2: Test with curl**
```bash
# Test the upload endpoint
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/path/to/test.txt" \
  -F "bucket=uploads"
```

**Expected Response:**
```json
{
  "url": "http://localhost:9000/uploads/abc123-test.txt",
  "key": "abc123-test.txt",
  "bucket": "uploads",
  "size": 1024,
  "filename": "test.txt",
  "content_type": "text/plain"
}
```

### Step 4: Test in Frontend

After restarting:
1. Go to Memories page
2. Click "Create Memory"
3. Try uploading a file
4. It should work now!

## Why This Happens

When you add new routes to FastAPI:
- The code is written to disk
- But the running server doesn't know about it
- You need to restart the server to load new routes
- The `--reload` flag helps, but sometimes you need a full restart

## Verify Route Registration

The route is properly configured:
- ✅ Route defined in `src/gml/api/routes/storage.py`
- ✅ Exported in `src/gml/api/routes/__init__.py`
- ✅ Imported in `src/gml/api/main.py`
- ✅ Registered with prefix `/api/v1`

Full endpoint path: `/api/v1` + `/storage` + `/upload` = `/api/v1/storage/upload`

## Still Not Working?

If restarting doesn't help:

1. **Check for Import Errors:**
   ```bash
   # Try importing the route manually
   cd src
   python3 -c "from gml.api.routes.storage import router; print('OK')"
   ```

2. **Check Server Logs:**
   - Look for any error messages when server starts
   - Check for "Routes configured successfully" message

3. **Verify Server is Running:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Check API Docs:**
   ```bash
   curl http://localhost:8000/api/openapi.json | grep storage
   ```

## Quick Test Script

Create a test file and upload it:

```bash
# Create test file
echo "Test content" > /tmp/test.txt

# Upload it
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/tmp/test.txt" \
  -F "bucket=uploads"
```

If this works, the route is available!

