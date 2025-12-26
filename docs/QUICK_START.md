# 🚀 Quick Start - GML Infrastructure

## ✅ What You Need (Simple Answer)

### ❌ You DON'T Need:
- **OpenRouter** - Not required
- **OpenAI API Key** - Optional (only for embeddings)
- **Any external APIs** - Everything runs locally

### ✅ You DO Need:
1. **Docker** (for local services)
2. **Run migrations** (create database tables)

## 🎯 3-Step Setup

### Step 1: Start Docker Services
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Step 2: Create Database Tables
```bash
# Generate migration (first time only)
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Step 3: Start Server
```bash
cd src
uvicorn gml.api.main:app --reload
```

## 🧪 Test It Works

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Register an agent
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "name": "My Agent",
    "version": "1.0.0",
    "description": "Test",
    "capabilities": ["test"]
  }'

# 3. Get the agent
curl http://localhost:8000/api/v1/agents/my-agent

# 4. List all agents
curl http://localhost:8000/api/v1/agents
```

## 📊 What Runs Where

| Service | Location | API Key? |
|---------|----------|----------|
| PostgreSQL | Docker (local) | ❌ No |
| Redis | Docker (local) | ❌ No |
| Qdrant | Docker (local) | ❌ No |
| MinIO | Docker (local) | ❌ No |
| OpenAI | External (optional) | ✅ Yes (only for embeddings) |

## 🎉 That's It!

No OpenRouter needed. No OpenAI needed (unless you want embeddings). Everything runs locally!

