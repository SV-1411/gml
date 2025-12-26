# How to Start the Server

## You Have a Virtual Environment!

You have a `venv` folder, which means you need to activate it first.

## Steps to Start Server:

### Step 1: Activate Virtual Environment

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### Step 2: Start the Server

```bash
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify Routes Loaded

Look for this message:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
```

## OR Use the Start Script

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./start_server.sh
```

This script will automatically:
- Try to activate venv
- Use the correct Python/uvicorn command

## If venv Doesn't Have uvicorn

If you get an error that uvicorn is not found after activating venv:

```bash
# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Then start server
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Quick One-Liner

```bash
cd "/Volumes/Yatri Cloud/org/gml/project" && source venv/bin/activate && cd src && uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## After Server Starts

1. You should see "Storage router registered" message
2. Test upload: `./test_upload.sh`
3. Check API docs: http://localhost:8000/api/docs

