# ✅ Working Examples - GML Infrastructure

## 🎯 Real Working Examples

This document provides **tested, working examples** for the GML Infrastructure API.

## 🚀 Quick Start

### 1. Ensure Server is Running
```bash
cd src
uvicorn gml.api.main:app --reload
```

### 2. Run Examples
```bash
# Simple bash examples
./SIMPLE_WORKING_EXAMPLE.sh

# Python examples
python test_working_examples.py
```

## ✅ Verified Working Endpoints

### 1. Health Check ✅
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-20T06:00:00Z"
}
```

### 2. API Information ✅
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "name": "GML Infrastructure API",
  "version": "0.1.0",
  "description": "Graph Machine Learning infrastructure service",
  "docs_url": "/api/docs",
  "redoc_url": "/api/redoc"
}
```

### 3. Prometheus Metrics ✅
```bash
curl http://localhost:8000/metrics
```

Returns Prometheus-formatted metrics.

## 📝 Example Workflow

### Step 1: Register an Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "name": "My Agent",
    "version": "1.0.0",
    "description": "My test agent",
    "capabilities": ["test"]
  }'
```

### Step 2: Get Agent Details
```bash
curl http://localhost:8000/api/v1/agents/my-agent
```

### Step 3: List All Agents
```bash
curl http://localhost:8000/api/v1/agents
```

## 🐍 Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Register agent
response = requests.post(
    f"{BASE_URL}/api/v1/agents/register",
    json={
        "agent_id": "python-agent",
        "name": "Python Test Agent",
        "version": "1.0.0",
        "description": "Test from Python",
        "capabilities": ["python", "test"]
    }
)
print(response.json())
```

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## ✅ Status

- ✅ Health endpoint working
- ✅ Root endpoint working  
- ✅ Metrics endpoint working
- ✅ API documentation accessible
- ✅ Server running and responding

## 🔧 Troubleshooting

If endpoints return 500 errors:
1. Check server logs: `tail -f /tmp/gml_server.log`
2. Verify Docker services: `docker-compose -f docker-compose.dev.yml ps`
3. Check database: `docker-compose -f docker-compose.dev.yml logs postgres`

## 📖 More Examples

See `WORKING_EXAMPLES.md` for detailed examples of all endpoints.

