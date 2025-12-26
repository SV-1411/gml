# Run This to Restart Server

## Quick Restart Command

Run this in your terminal:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./restart.sh
```

This will:
1. ✅ Stop the current server
2. ✅ Clear Python cache
3. ✅ Start the server fresh
4. ✅ Load all routes including storage

## OR Manual Restart

If the script doesn't work, do this manually:

### Step 1: Stop Server
In the terminal where server is running, press:
```
Ctrl+C
```

### Step 2: Start Server
```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## After Server Starts

Look for this in the output:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
```

Then test:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_upload.sh
```

## Status
- ✅ Route code is correct
- ✅ Route is registered
- ⚠️  Server needs restart to load route
- ✅ After restart, it will work!

