# Simple Start Command

## Copy and Paste This:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project" && source venv/bin/activate && lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 2 && cd src && uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## OR Use Script:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./RUN_THIS_NOW.sh
```

## What It Does:

1. ✅ Goes to project directory
2. ✅ Activates virtual environment
3. ✅ Kills old server on port 8000
4. ✅ Goes to `src` directory (IMPORTANT!)
5. ✅ Starts uvicorn from `src` directory

## After It Starts:

Look for:
```
INFO: Storage router registered at /api/v1/storage
```

Then file upload will work!

