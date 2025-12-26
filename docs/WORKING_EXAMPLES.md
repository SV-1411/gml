# 🎯 GML Infrastructure - Working Examples

## ✅ Real Working Examples

This document contains real, tested examples that work with the GML Infrastructure API.

## 🚀 Quick Start

### 1. Start the Server
```bash
cd src
uvicorn gml.api.main:app --reload
```

### 2. Run Tests
```bash
python test_working_examples.py
```

## 📝 Example 1: Register an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "weather-agent-001",
    "name": "Weather Service Agent",
    "version": "1.2.0",
    "description": "Provides weather forecasts",
    "capabilities": ["weather_forecast", "current_conditions"]
  }'
```

**Response:**
```json
{
  "agent_id": "weather-agent-001",
  "api_token": "gml_...",
  "public_key": "did:gml:..."
}
```

## 📝 Example 2: Get Agent Details

```bash
curl http://localhost:8000/api/v1/agents/weather-agent-001
```

**Response:**
```json
{
  "agent_id": "weather-agent-001",
  "name": "Weather Service Agent",
  "status": "inactive",
  "version": "1.2.0",
  "description": "Provides weather forecasts",
  "capabilities": ["weather_forecast", "current_conditions"],
  "created_at": "2025-12-20T06:00:00Z"
}
```

## 📝 Example 3: List All Agents

```bash
curl http://localhost:8000/api/v1/agents?limit=10
```

**Response:**
```json
{
  "agents": [...],
  "total": 2,
  "limit": 10,
  "offset": 0,
  "has_more": false
}
```

## 📝 Example 4: Write Memory

```bash
curl -X POST http://localhost:8000/api/v1/memory/write \
  -H "Content-Type: application/json" \
  -H "X-Agent-ID: weather-agent-001" \
  -d '{
    "conversation_id": "conv-001",
    "content": {
      "user_query": "What is the weather?",
      "response": "Sunny, 72°F"
    },
    "memory_type": "episodic",
    "visibility": "all",
    "tags": ["weather", "forecast"]
  }'
```

**Response:**
```json
{
  "context_id": "ctx-...",
  "version": 1,
  "embedding_dimensions": 1536
}
```

## 📝 Example 5: Search Memory

```bash
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -H "X-Agent-ID: weather-agent-001" \
  -d '{
    "query": "weather forecast",
    "limit": 5
  }'
```

**Response:**
```json
{
  "results": [
    {
      "context_id": "ctx-...",
      "content": {...},
      "similarity_score": 0.85,
      "created_by": "weather-agent-001",
      "created_at": "2025-12-20T06:00:00Z"
    }
  ]
}
```

## 📝 Example 6: Health Check

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

## 📝 Example 7: Detailed Health

```bash
curl http://localhost:8000/api/v1/health/detailed
```

**Response:**
```json
{
  "detail": {
    "overall_status": "healthy",
    "services": {
      "database": {"status": "healthy"},
      "redis": {"status": "healthy"},
      "qdrant": {"status": "healthy"}
    }
  }
}
```

## 📝 Example 8: Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

**Response:**
```
# HELP gml_agents_registered_total Total number of agents registered
# TYPE gml_agents_registered_total counter
gml_agents_registered_total 2.0
...
```

## 🐍 Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Register agent
response = requests.post(
    f"{BASE_URL}/api/v1/agents/register",
    json={
        "agent_id": "my-agent",
        "name": "My Agent",
        "version": "1.0.0",
        "description": "My test agent",
        "capabilities": ["test"]
    }
)
print(response.json())

# Get agent
response = requests.get(f"{BASE_URL}/api/v1/agents/my-agent")
print(response.json())
```

## ✅ All Examples Tested and Working!

Run `python test_working_examples.py` to see all examples in action.

