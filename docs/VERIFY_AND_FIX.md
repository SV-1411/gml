# Verify and Fix Backend Routes

## Quick Verification Steps

### Step 1: Check if Routes are Registered

Open your browser and go to:
```
http://localhost:8000/api/docs
```

**Look for:**
1. **storage** section with:
   - `POST /api/v1/storage/upload`
   - `GET /api/v1/storage/url/{key}`

2. **agents** section with:
   - `PATCH /api/v1/agents/{agent_id}/status`

**If you DON'T see these routes:**
→ Your server needs to be restarted (see Step 2)

### Step 2: Force Server Restart

**IMPORTANT:** You MUST fully restart the backend server for new routes to load.

```bash
# 1. Stop the server (find terminal with uvicorn, press Ctrl+C)

# 2. Clear Python cache (optional but recommended)
cd "/Volumes/Yatri Cloud/org/gml/project"
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true

# 3. Restart server
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Watch for these messages:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Routes configured successfully  ← This is important!
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test Routes Directly

**Test Storage Upload:**
```bash
# Create test file
echo "test content" > /tmp/test.txt

# Upload it
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/tmp/test.txt" \
  -F "bucket=uploads"
```

**Expected Success Response:**
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

**Test Agent Status:**
```bash
curl -X PATCH http://localhost:8000/api/v1/agents/YOUR_AGENT_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

### Step 4: Check for Import Errors

If routes still don't appear, check server logs for errors:

**Common errors:**
- `ModuleNotFoundError` - Missing dependency
- `ImportError` - Import path issue
- `SyntaxError` - Code syntax error

**Fix import errors:**
```bash
# Install missing dependencies
pip install minio

# Verify imports work
cd src
python3 -c "from gml.api.routes import storage_router; print('OK')"
```

## Route Configuration Summary

✅ **Storage Route:**
- File: `src/gml/api/routes/storage.py`
- Router prefix: `/storage`
- Full path: `/api/v1/storage/upload`
- Registered in: `src/gml/api/main.py` line 243

✅ **Agent Status Route:**
- File: `src/gml/api/routes/agents.py`
- Router prefix: `/agents`
- Full path: `/api/v1/agents/{agent_id}/status`
- Registered in: `src/gml/api/main.py` line 240

## Troubleshooting

### Problem: Routes still not found after restart

**Solution 1: Check server logs**
- Look for "Routes configured successfully" message
- Check for any error messages during startup

**Solution 2: Verify route files exist**
```bash
ls -la src/gml/api/routes/storage.py
ls -la src/gml/api/routes/agents.py
```

**Solution 3: Test route import**
```bash
cd src
python3 -c "
from gml.api.routes.storage import router as storage_router
from gml.api.routes.agents import router as agents_router
print('Routes import OK')
"
```

**Solution 4: Check route registration order**

In `src/gml/api/main.py`, ensure routes are included:
```python
app.include_router(agents_router, prefix="/api/v1")
app.include_router(storage_router, prefix="/api/v1")
```

### Problem: File upload works but MinIO errors

**Solution:** Install MinIO client:
```bash
pip install minio
```

Or the route will use placeholder URLs (still works, just files won't actually be stored).

### Problem: Agent activation works but file upload doesn't

**Check:**
1. Both routes should be in `/api/docs`
2. If one works but not the other, check individual route files
3. Verify both are in `__init__.py` exports

## Complete Fix Script

```bash
#!/bin/bash
# Complete fix script

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "1. Clearing Python cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true

echo "2. Installing dependencies..."
pip install minio > /dev/null 2>&1 || echo "MinIO already installed"

echo "3. Verifying route files exist..."
ls -la src/gml/api/routes/storage.py
ls -la src/gml/api/routes/agents.py

echo "4. Testing route imports..."
cd src
python3 -c "
try:
    from gml.api.routes import storage_router, agents_router
    print('✅ Routes import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "✅ Setup complete!"
echo "Now restart your server:"
echo "  cd src"
echo "  uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
```

