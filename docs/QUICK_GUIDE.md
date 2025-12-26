# Quick Guide: MinIO Login & Agent Activation

## MinIO Login Instructions

### Access MinIO Console

1. **Start MinIO** (if using Docker Compose):
   ```bash
   docker-compose up -d minio
   ```

2. **Open MinIO Console in Browser**:
   - URL: http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin`

3. **Login Steps**:
   - Navigate to http://localhost:9001 in your browser
   - Enter username: `minioadmin`
   - Enter password: `minioadmin`
   - Click "Login"

### MinIO Configuration

**Default Settings:**
- Console URL: http://localhost:9001
- API URL: http://localhost:9000
- Root User: `minioadmin`
- Root Password: `minioadmin`

**Buckets Available:**
- `uploads` - For user file uploads (public download)
- `backups` - For backup files
- `models` - For AI model files

### Change MinIO Credentials (Production)

Edit `.env` file or `docker-compose.yml`:
```yaml
environment:
  MINIO_ROOT_USER: your-username
  MINIO_ROOT_PASSWORD: your-secure-password
```

---

## Agent Activation Instructions

### Method 1: Using Frontend UI

1. **Register an Agent** (if not already registered):
   - Go to "Agents" page in frontend
   - Click "Register Agent"
   - Fill in the form and register
   - Note: New agents start with status "inactive"

2. **Activate Agent**:
   - Go to "Agents" page
   - Click on the agent you want to activate
   - Click "Activate" button (or update status dropdown)
   - Agent status will change to "active"

### Method 2: Using API

**Activate Agent via API:**

```bash
# Update agent status to "active"
curl -X PATCH http://localhost:8000/api/v1/agents/{agent_id}/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

**Example:**
```bash
curl -X PATCH http://localhost:8000/api/v1/agents/my-agent-001/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

**Response:**
```json
{
  "agent_id": "my-agent-001",
  "name": "My AI Agent",
  "status": "active",
  "last_heartbeat": "2024-01-15T10:30:00Z"
}
```

### Method 3: Using Python Script

```python
import requests

# Update agent status
agent_id = "my-agent-001"
url = f"http://localhost:8000/api/v1/agents/{agent_id}/status"
payload = {"status": "active"}

response = requests.patch(url, json=payload)
print(response.json())
```

### Agent Status Values

- **`inactive`** - Default status for new agents (not operational)
- **`active`** - Agent is active and operational
- **`error`** - Agent encountered an error
- **`maintenance`** - Agent is in maintenance mode

### Verify Agent Status

**Check agent status:**
```bash
curl http://localhost:8000/api/v1/agents/my-agent-001
```

**List all active agents:**
```bash
curl http://localhost:8000/api/v1/agents?status=active
```

---

## Complete Setup Workflow

### 1. Start Services

```bash
# Start all services (including MinIO)
docker-compose up -d

# Or start individually
docker-compose up -d postgres redis qdrant minio
```

### 2. Access MinIO

1. Open http://localhost:9001
2. Login with `minioadmin` / `minioadmin`
3. Verify buckets are created (uploads, backups, models)

### 3. Register Agent

**Via Frontend:**
- Go to http://localhost:3000/agents
- Click "Register Agent"
- Fill form and save API token

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent-001",
    "name": "My AI Agent",
    "version": "1.0.0",
    "description": "Test agent",
    "capabilities": ["chat", "file_processing"]
  }'
```

### 4. Activate Agent

**Via Frontend:**
- Go to Agents page
- Find your agent
- Change status to "active"

**Via API:**
```bash
curl -X PATCH http://localhost:8000/api/v1/agents/my-agent-001/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

### 5. Verify Activation

```bash
# Check agent details
curl http://localhost:8000/api/v1/agents/my-agent-001
```

Look for:
- `"status": "active"`
- `"last_heartbeat"` should have a timestamp

---

## Troubleshooting

### MinIO Not Accessible

**Problem:** Cannot access http://localhost:9001

**Solutions:**
1. Check if MinIO is running:
   ```bash
   docker ps | grep minio
   ```

2. Check MinIO logs:
   ```bash
   docker logs gml-minio
   ```

3. Restart MinIO:
   ```bash
   docker-compose restart minio
   ```

### Agent Won't Activate

**Problem:** Agent status remains "inactive"

**Solutions:**
1. Verify agent exists:
   ```bash
   curl http://localhost:8000/api/v1/agents/{agent_id}
   ```

2. Check API response for errors

3. Verify you're using correct agent_id

4. Check backend logs for errors

### Agent Status API Returns 404

**Problem:** PATCH endpoint not found

**Solution:** The status update endpoint may need to be added. Check if the route exists in `src/gml/api/routes/agents.py`

---

## Additional Resources

- **MinIO Documentation:** https://min.io/docs/
- **API Documentation:** http://localhost:8000/api/docs
- **Frontend Dashboard:** http://localhost:3000

