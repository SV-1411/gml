# How to Start Server Correctly

## The Error
```
ModuleNotFoundError: No module named 'gml'
```

This happens because uvicorn can't find the `gml` module.

## The Fix

You MUST run uvicorn from the `src` directory!

### Correct Command:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
source venv/bin/activate
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### OR Use the Fixed Script:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./start_server_fixed.sh
```

## Why This Works

The `gml` module is located in `src/gml/`, so you need to:
1. Be in the `src` directory
2. Run `uvicorn gml.api.main:app` (not `src.gml.api.main:app`)

## After Server Starts

Look for:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
```

Then test:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_upload.sh
```

