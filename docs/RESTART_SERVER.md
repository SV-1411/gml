# Fix: Endpoints Not Found - RESTART SERVER

## Problem
Both endpoints are returning "not found" errors:
- `Endpoint /api/v1/agents/{agent_id}/status not found`
- `Endpoint /api/v1/storage/upload not found`

## Root Cause
These routes were recently added to the code but the backend server hasn't been restarted to load them.

## Solution: Restart Backend Server

### Step 1: Stop Current Server

1. Find the terminal where your backend server is running
2. Press `Ctrl+C` to stop it
3. Wait for it to fully stop

### Step 2: Restart Server

```bash
# Navigate to project directory
cd "/Volumes/Yatri Cloud/org/gml/project/src"

# Start the server
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Wait for Startup

Look for these messages in the terminal:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

You should also see:
```
INFO:     Routes configured successfully
```

### Step 4: Verify Routes are Available

**Check API Documentation:**
```bash
# Open in browser
open http://localhost:8000/api/docs
```

Look for:
1. **storage** section with:
   - `POST /api/v1/storage/upload`
   - `GET /api/v1/storage/url/{key}`

2. **agents** section with:
   - `PATCH /api/v1/agents/{agent_id}/status`
   - `POST /api/v1/agents/register`
   - `GET /api/v1/agents/{agent_id}`
   - `GET /api/v1/agents`

### Step 5: Test Endpoints

**Test Agent Status Update:**
```bash
curl -X PATCH http://localhost:8000/api/v1/agents/weather-ollama-test/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

**Expected Response:**
```json
{
  "agent_id": "weather-ollama-test",
  "name": "...",
  "status": "active",
  ...
}
```

**Test File Upload:**
```bash
# Create test file
echo "Test content" > /tmp/test.txt

# Upload it
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/tmp/test.txt" \
  -F "bucket=uploads"
```

**Expected Response:**
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

## Why Restart is Needed

When you add new routes to FastAPI:
- The route definitions exist in the code files
- But the running Python process doesn't know about them
- The server needs to reload the application code
- This happens automatically with `--reload` flag, but sometimes you need a full restart

## If Still Not Working After Restart

### Check 1: Import Errors

Look at the server startup logs. If you see import errors, fix them:

```bash
# Common issues:
# - Missing dependencies: pip install minio
# - Syntax errors in route files
# - Import path issues
```

### Check 2: Route Registration

Verify routes are in the correct order in `src/gml/api/main.py`:

```python
# Should include:
app.include_router(agents_router, prefix="/api/v1")
app.include_router(storage_router, prefix="/api/v1")
```

### Check 3: Verify Route Files Exist

```bash
ls -la src/gml/api/routes/
# Should show:
# - agents.py
# - storage.py
# - memory.py
# - ollama.py
# - health.py
```

### Check 4: Test Route Import

```bash
cd src
python3 -c "from gml.api.routes import agents_router, storage_router; print('Routes imported OK')"
```

If this fails, there's an import error to fix.

## Quick Verification Checklist

After restarting:
- [ ] Server shows "Application startup complete"
- [ ] No error messages in server logs
- [ ] `/api/docs` shows storage routes
- [ ] `/api/docs` shows PATCH agent status route
- [ ] `curl` tests work for both endpoints
- [ ] Frontend can activate agents
- [ ] Frontend can upload files

## Still Having Issues?

1. **Check Server Logs:**
   - Look for error messages during startup
   - Check for import errors
   - Verify "Routes configured successfully" appears

2. **Clear Python Cache:**
   ```bash
   find src -type d -name __pycache__ -exec rm -r {} +
   find src -name "*.pyc" -delete
   ```

3. **Full Restart:**
   ```bash
   # Stop server completely
   # Remove cache
   # Restart server
   ```

