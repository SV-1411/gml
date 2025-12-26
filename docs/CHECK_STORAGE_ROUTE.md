# Storage Route Check

## Issue: Endpoint /api/v1/storage/upload not found

### Solution Steps:

1. **Restart Backend Server**
   The storage route was just added. You need to restart the backend server:
   
   ```bash
   # Stop the current server (Ctrl+C)
   # Then restart:
   cd src
   uvicorn gml.api.main:app --reload
   ```

2. **Verify Route is Registered**
   
   After restarting, check if the route exists:
   
   ```bash
   # Check API documentation
   open http://localhost:8000/api/docs
   
   # Look for "storage" tag in the API docs
   # You should see:
   # - POST /api/v1/storage/upload
   # - GET /api/v1/storage/url/{key}
   ```

3. **Test the Endpoint**
   
   ```bash
   # Test upload endpoint
   curl -X POST http://localhost:8000/api/v1/storage/upload \
     -F "file=@test.txt" \
     -F "bucket=uploads"
   ```

4. **Check Server Logs**
   
   When you start the server, you should see:
   ```
   Routes configured successfully
   ```
   
   If you see import errors, check:
   - Is `minio` package installed? `pip install minio`
   - Are there any Python syntax errors in storage.py?

### Common Issues:

**Issue 1: Server Not Restarted**
- **Symptom:** Route not found even though code exists
- **Solution:** Restart the backend server

**Issue 2: Import Error**
- **Symptom:** Server fails to start or route not loaded
- **Solution:** Check server logs for import errors

**Issue 3: Route Path Mismatch**
- **Symptom:** 404 error
- **Solution:** Verify the route prefix matches: `/api/v1/storage`

### Quick Fix:

```bash
# 1. Stop current server (if running)
# Press Ctrl+C in the terminal running uvicorn

# 2. Restart server
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000

# 3. Wait for "Application startup complete" message

# 4. Test the endpoint
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/path/to/test.txt" \
  -F "bucket=uploads"
```

### Verify Route Registration:

The storage router should be registered in:
- `src/gml/api/routes/__init__.py` - exports `storage_router`
- `src/gml/api/main.py` - imports and includes `storage_router` with prefix `/api/v1`

The full endpoint path will be:
- `/api/v1` (from main.py) + `/storage` (from router prefix) + `/upload` (from route) = `/api/v1/storage/upload`

