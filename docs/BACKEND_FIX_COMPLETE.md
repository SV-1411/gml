# Backend Routes - Complete Fix Guide

## Problem
- ❌ File upload: `Endpoint /api/v1/storage/upload not found`
- ❌ Agent activation: `Endpoint /api/v1/agents/{id}/status not found`

## Root Cause
Backend server hasn't been restarted to load the newly added routes.

## ✅ Solution: Complete Fix

### Method 1: Quick Fix Script (Recommended)

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./fix_routes.sh
```

This script will:
1. Clear Python cache
2. Install dependencies (minio)
3. Verify route files exist
4. Test route imports
5. Give you next steps

### Method 2: Manual Fix

#### Step 1: Stop Current Server
Find terminal running `uvicorn` and press `Ctrl+C`

#### Step 2: Clear Cache (Optional but Recommended)
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true
```

#### Step 3: Install Dependencies
```bash
pip install minio
```

#### Step 4: Restart Server
```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 5: Verify Routes

**Option A: Check API Docs**
```bash
open http://localhost:8000/api/docs
```

Look for:
- ✅ **storage** section with `POST /api/v1/storage/upload`
- ✅ **agents** section with `PATCH /api/v1/agents/{agent_id}/status`

**Option B: Test with curl**
```bash
# Test storage upload
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/path/to/test.txt" \
  -F "bucket=uploads"

# Test agent status
curl -X PATCH http://localhost:8000/api/v1/agents/YOUR_AGENT_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

## ✅ Routes Configuration Verified

Both routes are properly configured:

### Storage Route
- **File:** `src/gml/api/routes/storage.py` ✅
- **Router:** `APIRouter(prefix="/storage")` ✅
- **Endpoint:** `POST /upload` ✅
- **Registered:** `main.py` line 243 ✅
- **Full path:** `/api/v1/storage/upload` ✅

### Agent Status Route
- **File:** `src/gml/api/routes/agents.py` ✅
- **Router:** `APIRouter(prefix="/agents")` ✅
- **Endpoint:** `PATCH /{agent_id}/status` ✅
- **Registered:** `main.py` line 240 ✅
- **Full path:** `/api/v1/agents/{agent_id}/status` ✅

## Verification Checklist

After restarting server, verify:

- [ ] Server shows "Application startup complete"
- [ ] Server shows "Routes configured successfully"
- [ ] No error messages in server logs
- [ ] http://localhost:8000/api/docs shows "storage" section
- [ ] http://localhost:8000/api/docs shows PATCH in "agents" section
- [ ] curl test for storage upload works
- [ ] curl test for agent status works
- [ ] Frontend can upload files
- [ ] Frontend can activate agents

## Troubleshooting

### Routes Still Not Found After Restart

1. **Check server logs for errors:**
   - Import errors
   - Syntax errors
   - Missing dependencies

2. **Verify route files exist:**
   ```bash
   ls -la src/gml/api/routes/storage.py
   ls -la src/gml/api/routes/agents.py
   ```

3. **Test route imports:**
   ```bash
   cd src
   python3 -c "from gml.api.routes import storage_router, agents_router; print('OK')"
   ```

4. **Check route registration:**
   - Open `src/gml/api/main.py`
   - Verify lines 240 and 243 include the routers

### Import Errors

If you see import errors in logs:

```bash
# Install missing dependencies
pip install minio

# Verify installation
python3 -c "import minio; print('MinIO installed')"
```

### Server Won't Start

1. Check Python version: `python3 --version` (should be 3.11+)
2. Install dependencies: `pip install -r requirements.txt`
3. Check for syntax errors: `python3 -m py_compile src/gml/api/routes/storage.py`

## Quick Test Commands

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Test storage upload
echo "test" > /tmp/test.txt
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/tmp/test.txt" \
  -F "bucket=uploads"

# 3. Test agent status
curl -X PATCH http://localhost:8000/api/v1/agents/YOUR_AGENT_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'

# 4. Check API docs
curl http://localhost:8000/api/openapi.json | grep -i storage
```

## Summary

**Everything is configured correctly in the code.**

You just need to:
1. ✅ Stop the server
2. ✅ Restart the server
3. ✅ Verify routes appear in /api/docs

The routes will work immediately after restart!

