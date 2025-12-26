# Run This Command

Copy and paste this into your terminal:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project" && source venv/bin/activate && cd src && uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

OR use the script:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./quick_start.sh
```

## What This Does:

1. ✅ Goes to project directory
2. ✅ Activates virtual environment (venv)
3. ✅ Goes to src directory
4. ✅ Starts the server with uvicorn

## After Server Starts:

Look for:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
```

Then the file upload will work!
