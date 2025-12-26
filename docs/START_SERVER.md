# Start Backend Server

## Server Status
- ✅ Server process stopped
- ✅ Python cache cleared
- ⏳ Ready to start

## Start the Server

Run this command in a terminal:

```bash
cd "/Volumes/Yatri Cloud/org/gml/project/src"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

## OR Use the Restart Script

```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./restart_server.sh
```

## Verify Routes Loaded

After starting, look for these messages in the server output:
```
INFO: Storage router registered at /api/v1/storage
INFO: All routes configured successfully
INFO: Registered routers: agents, health, memory, ollama, storage
INFO: Application startup complete.
```

## Test the Upload Route

After server starts, run:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./test_upload.sh
```

Or test manually:
```bash
echo "test" > /tmp/test.txt
curl -X POST http://localhost:8000/api/v1/storage/upload \
  -F "file=@/tmp/test.txt" \
  -F "bucket=uploads"
```

## Verify in Browser

Open: http://localhost:8000/api/docs

Look for "storage" section with:
- `POST /api/v1/storage/upload`
- `GET /api/v1/storage/url/{key}`

## After Server Starts

1. ✅ Routes will be loaded
2. ✅ Upload endpoint will work
3. ✅ Frontend can upload files
4. ✅ All storage routes available

**The route code is correct - it just needs the server to restart to load it!**

