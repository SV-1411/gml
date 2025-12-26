# Stop and Restart Server - Commands

## Current Status
Server is running but route is NOT loaded. You need to manually restart it.

## Option 1: Stop and Restart Manually

### Step 1: Stop Server
Find the terminal window where `uvicorn` is running and press:
```
Ctrl+C
```

Wait until you see the server stop (it will say "Shutting down" or return to command prompt).

### Step 2: Restart Server
Run this command in the same terminal or a new terminal:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify Routes Loaded
Look for these messages:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
INFO: Registered routers: agents, health, memory, ollama, storage
```

## Option 2: Use Kill Command (if Ctrl+C doesn't work)

### Stop Server:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Verify it's stopped
curl http://localhost:8000/health
# Should say: connection refused or timeout
```

### Start Server:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Option 3: Use the Script (Background)

If you want to restart in background:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./restart_server.sh
```

## After Restart - Verify

### Test Upload Route:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_upload.sh
```

### Or Manual Test:
```bash
echo "test content" > /tmp/test.txt
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

## Check in Browser

Open: http://localhost:8000/api/docs

You should see **"storage"** section with the upload endpoint.

## Important Notes

1. **The route code is correct** ✅
2. **Server just needs to reload the code** ⚠️
3. **After restart, it will work immediately** ✅

The verification script confirmed:
- ✅ Route files exist
- ✅ Routes are defined
- ✅ Routes are registered in code
- ❌ Routes NOT loaded in running server (needs restart)

