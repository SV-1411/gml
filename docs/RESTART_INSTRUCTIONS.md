# Restart Server Instructions

## Current Status
The server is running but the storage route is NOT loaded yet.

## How to Restart

### Method 1: Using Terminal (Recommended)

1. **Find the terminal window where your server is running**
   - Look for a terminal showing uvicorn logs
   - Or check which terminal has the process

2. **Stop the server:**
   - Press `Ctrl+C` in that terminal
   - Wait until it stops (you'll see "Shutting down" or return to prompt)

3. **Restart the server:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project/src"
   uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Verify routes loaded:**
   Look for these messages in the output:
   ```
   INFO: Storage router registered at /api/v1/storage
   INFO: All routes configured successfully
   INFO: Registered routers: agents, health, memory, ollama, storage
   ```

### Method 2: Kill Process and Restart

If Ctrl+C doesn't work:

1. **Kill the server process:**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Wait a few seconds, then start:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project/src"
   uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Method 3: If Using Python Virtual Environment

If you're using a virtual environment:

1. **Activate it first:**
   ```bash
   source venv/bin/activate  # or your venv path
   ```

2. **Then restart:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project/src"
   uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## After Restart - Verify

### Test 1: Check API Docs
Open in browser: http://localhost:8000/api/docs

Look for **"storage"** section with:
- `POST /api/v1/storage/upload`
- `GET /api/v1/storage/url/{key}`

### Test 2: Test Upload
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_upload.sh
```

### Test 3: Manual Test
```bash
echo "test" > /tmp/test.txt
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/tmp/test.txt" \
  -F "bucket=uploads"
```

**Expected response:**
```json
{
  "url": "http://localhost:9000/uploads/abc123-test.txt",
  "key": "abc123-test.txt",
  "bucket": "uploads",
  "size": 5,
  "filename": "test.txt",
  "content_type": "text/plain"
}
```

## Why Restart is Needed

- ✅ Route code exists and is correct
- ✅ Route is exported and registered in code
- ❌ Running server process hasn't loaded the new route yet
- ✅ After restart, route will be available immediately

## Quick Checklist

- [ ] Server stopped (Ctrl+C or kill command)
- [ ] Server restarted (uvicorn command)
- [ ] See "Storage router registered" in logs
- [ ] Route appears in http://localhost:8000/api/docs
- [ ] Test upload works
- [ ] Frontend can upload files

## Still Not Working?

1. Check server logs for errors
2. Verify Python version: `python3 --version` (should be 3.11+)
3. Install dependencies: `pip install -r requirements.txt`
4. Check for syntax errors in route files

