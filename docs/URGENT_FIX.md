# URGENT: Fix Storage Upload Route

## The Problem
The route exists in code but the server hasn't loaded it.

## IMMEDIATE ACTION REQUIRED

### Step 1: STOP Your Server
1. Find the terminal running your backend
2. Press `Ctrl+C` to stop it
3. **WAIT** until it completely stops

### Step 2: RESTART Your Server
```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: CHECK Server Logs
Look for these messages:
```
INFO: Routes configured successfully
INFO: Registered routers: agents, health, memory, ollama, storage
```

**If you DON'T see "storage" in the list, there's an import error.**

### Step 4: VERIFY Route is Available

**Open in browser:**
```
http://localhost:8000/api/docs
```

**Click on "storage" section** - you should see:
- `POST /api/v1/storage/upload`
- `GET /api/v1/storage/url/{key}`

**If you DON'T see the storage section:**
1. Check server logs for errors
2. Look for "ImportError" or "ModuleNotFoundError"
3. The route file might have a syntax error

## Quick Test

After restarting, test the endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/dev/null" \
  -F "bucket=uploads"
```

**Expected:** JSON response with URL
**If 404:** Server didn't load the route (check logs)

## Why This Happens

When you add new routes:
1. Code is written to disk ✅
2. But the running Python process doesn't reload automatically ❌
3. Even with `--reload`, sometimes you need a FULL restart
4. The server must re-import all modules to see new routes

## Still Not Working?

If the route still doesn't appear after restart:

1. **Check for Import Errors:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project/src"
   python3 -c "from gml.api.routes.storage import router; print('OK')"
   ```

2. **Check Server Logs:**
   - Look for any error messages during startup
   - Check for "Failed to import routers"
   - Check for syntax errors

3. **Verify File Exists:**
   ```bash
   ls -la "/Volumes/Yatri Cloud/org/gml/project/src/gml/api/routes/storage.py"
   ```

4. **Test Route Registration:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project/src"
   python3 << 'EOF'
   from gml.api.main import app
   routes = [r.path for r in app.routes]
   storage_routes = [r for r in routes if 'storage' in r]
   print("Storage routes found:", storage_routes)
   EOF
   ```

## The Route IS Configured Correctly

- ✅ File exists: `src/gml/api/routes/storage.py`
- ✅ Router defined: `router = APIRouter(prefix="/storage")`
- ✅ Route defined: `@router.post("/upload")`
- ✅ Exported: `src/gml/api/routes/__init__.py`
- ✅ Imported: `src/gml/api/main.py` line 234
- ✅ Registered: `src/gml/api/main.py` line 243

**Everything is correct - you just need to restart!**

