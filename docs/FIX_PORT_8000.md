# Fix: Port 8000 Already in Use

## Problem
Error: `[Errno 48] Address already in use`

This means the old server is still running on port 8000.

## Quick Fix

### Option 1: Use the Kill and Restart Script (Easiest)

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./kill_and_restart.sh
```

This will:
1. ✅ Kill the old server
2. ✅ Clear cache
3. ✅ Activate venv
4. ✅ Start fresh server

### Option 2: Manual Fix

**Step 1: Kill the old server**
```bash
lsof -ti:8000 | xargs kill -9
```

**Step 2: Verify port is free**
```bash
curl http://localhost:8000/health
# Should say: connection refused
```

**Step 3: Start server**
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
source venv/bin/activate
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## After Server Starts

Look for these messages:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
```

## Verify Storage Routes

After server starts, test:
```bash
curl -s http://localhost:8000/api/openapi.json | grep "storage/upload"
```

Should show: `"/api/v1/storage/upload"`

Then test upload:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_upload.sh
```

## One-Liner Command

```bash
cd "/Volumes/Yatri Cloud/org/gml/project" && lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 2; source venv/bin/activate && cd src && uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

