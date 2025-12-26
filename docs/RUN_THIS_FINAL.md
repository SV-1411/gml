# Final Working Command

## Copy and Paste This:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project" && source venv/bin/activate && lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 2 && export PYTHONPATH="${PYTHONPATH}:$(pwd)/src" && uvicorn src.gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## OR Use the Script:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./START_SERVER_FIXED.sh
```

## What's Different:

The imports use `from src.gml...` format, so:
1. ✅ Run from **project root** (not src directory)
2. ✅ Set `PYTHONPATH` to include `src` directory
3. ✅ Use `src.gml.api.main:app` as the module path

## After Server Starts:

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

