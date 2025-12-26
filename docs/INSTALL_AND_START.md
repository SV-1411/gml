# Install Dependencies and Start Everything

## Step 1: Install Missing Dependencies

Run this command:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
source venv/bin/activate
pip install python-multipart minio
```

## Step 2: Start MinIO Docker

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./start_minio.sh
```

OR manually:
```bash
docker-compose -f docker-compose.dev.yml up -d minio
```

## Step 3: Start Backend Server

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
source venv/bin/activate
lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 2
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
uvicorn src.gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## OR Use the Fixed Script:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./START_SERVER_FIXED.sh
```

## After Server Starts:

Look for:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
```

No more errors about:
- ❌ python-multipart (now installed)
- ❌ minio client (now installed)

## Verify:

1. **Check MinIO:**
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

2. **Check Server:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Test Upload:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project"
   ./test_upload.sh
   ```

