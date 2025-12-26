# Quick Restart Instructions

## The Problem
Route exists in code but server hasn't loaded it.

## The Solution
Restart the server.

## Commands to Run:

### 1. Stop Server (in the terminal running uvicorn):
Press: `Ctrl+C`

### 2. Start Server:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Verify (look for this in output):
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
```

### 4. Test:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_upload.sh
```

## That's It!

After restart, file upload will work.
