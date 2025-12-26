# Troubleshooting Guide

## Agent Activation Error

If you see "Failed to activate agent. Please try again." error:

### Check 1: Backend Server Running

```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","version":"0.1.0"}
```

**Solution:** If not running, start the backend:
```bash
cd src
uvicorn gml.api.main:app --reload
```

### Check 2: Agent Exists

```bash
# Check if agent exists
curl http://localhost:8000/api/v1/agents/{agent_id}

# Replace {agent_id} with your actual agent ID
```

**Solution:** If agent doesn't exist, register it first via UI or API.

### Check 3: Backend Logs

Check backend console for error messages:
- Look for error details when activation fails
- Common errors:
  - `AgentNotFoundError` - Agent ID doesn't exist
  - `InvalidAgentStatusError` - Invalid status value
  - Database connection errors

### Check 4: Network Issues

**Browser Console:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed requests
- Look at the failed request's response

**Common Issues:**
- CORS errors
- Network timeout
- 404 Not Found (endpoint doesn't exist)
- 500 Internal Server Error (backend error)

### Check 5: API Endpoint

Verify the status update endpoint exists:
```bash
# Test the endpoint directly
curl -X PATCH http://localhost:8000/api/v1/agents/test-agent-001/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

**Expected Response:**
```json
{
  "agent_id": "test-agent-001",
  "name": "Test Agent",
  "status": "active",
  ...
}
```

### Check 6: Frontend API Call

Check if frontend is making correct API call:
1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "Activate" button
4. Find the PATCH request to `/api/v1/agents/{id}/status`
5. Check:
   - Request URL is correct
   - Request payload: `{"status": "active"}`
   - Response status code
   - Response body for error details

### Manual Fix

If UI doesn't work, activate via API:

```bash
# Activate agent
curl -X PATCH http://localhost:8000/api/v1/agents/YOUR_AGENT_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

Replace `YOUR_AGENT_ID` with your actual agent ID.

---

## MinIO Setup Issues

### MinIO Not Starting

**Problem:** MinIO container fails to start

**Check:**
```bash
docker logs gml-minio
docker ps | grep minio
```

**Solution:**
```bash
# Restart MinIO
docker-compose -f docker-compose.dev.yml restart minio

# Or remove and recreate
docker-compose -f docker-compose.dev.yml up -d minio
```

### Cannot Access MinIO Console

**Problem:** Cannot access http://localhost:9001

**Check:**
1. Port 9001 is not in use:
   ```bash
   lsof -i :9001
   ```

2. MinIO container is running:
   ```bash
   docker ps | grep minio
   ```

**Solution:**
```bash
# Check container status
docker ps -a | grep minio

# If stopped, start it
docker start gml-minio

# Check logs
docker logs gml-minio
```

### File Upload Returns Error

**Problem:** File upload fails with error

**Check:**
1. MinIO is accessible:
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

2. Bucket exists (check MinIO console)

3. Backend can connect to MinIO:
   - Check backend logs
   - Look for MinIO connection errors

**Solution:**

**Option 1: Install MinIO Python Client**
```bash
pip install minio
```

**Option 2: Use Placeholder URLs**
- The system works without MinIO
- Files will have placeholder URLs
- Actual file storage won't work, but API won't fail

### MinIO Python Client Not Installed

**Problem:** Error about minio module not found

**Solution:**
```bash
# Install MinIO client
pip install minio

# Or add to requirements.txt
echo "minio" >> requirements.txt
pip install -r requirements.txt
```

---

## General Issues

### Database Connection Errors

**Problem:** Cannot connect to database

**Check:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database connection
psql -h localhost -U postgres -d gml_db
```

**Solution:**
```bash
# Start PostgreSQL
docker-compose -f docker-compose.dev.yml up -d postgres

# Check logs
docker logs gml-postgres
```

### Frontend Not Loading

**Problem:** Frontend shows blank page or errors

**Check:**
1. Frontend server is running:
   ```bash
   curl http://localhost:3000
   ```

2. Browser console for errors

3. Backend API is accessible:
   ```bash
   curl http://localhost:8000/health
   ```

**Solution:**
```bash
# Start frontend
cd frontend
npm install
npm run dev
```

### API CORS Errors

**Problem:** CORS errors in browser console

**Check:** Backend CORS configuration in `src/gml/api/main.py`

**Solution:** Ensure CORS middleware is configured to allow frontend origin.

---

## Getting Help

1. **Check Logs:**
   - Backend: Terminal where uvicorn is running
   - Frontend: Browser console
   - Docker: `docker logs <container_name>`

2. **Verify Services:**
   ```bash
   # Check all services
   docker ps
   
   # Check specific service
   docker logs gml-postgres
   docker logs gml-redis
   docker logs gml-minio
   ```

3. **Test API:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # API docs
   open http://localhost:8000/api/docs
   ```

4. **Check Configuration:**
   - Verify `.env` file exists
   - Check environment variables
   - Verify port numbers match

