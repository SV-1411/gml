# 🧪 Complete Testing Guide - GML Infrastructure

## 🎯 What You Need to Know

### ❌ You DON'T Need:
- **OpenRouter** - Not required
- **OpenAI API Key** - Optional (only for embeddings)
- **External APIs** - Everything runs locally

### ✅ You DO Need:
- **Docker** - For PostgreSQL, Redis, Qdrant, MinIO
- **Python 3.11+** - Already installed
- **That's it!** - Everything else is local

## 🚀 Quick Start Testing

### Step 1: Start Services
```bash
# Start all Docker services
docker-compose -f docker-compose.dev.yml up -d

# Wait 10 seconds for services to start
sleep 10

# Verify services are running
docker-compose -f docker-compose.dev.yml ps
```

### Step 2: Start API Server
```bash
cd src
uvicorn gml.api.main:app --reload
```

### Step 3: Test Basic Endpoints

#### Test 1: Health Check ✅
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status": "healthy", "timestamp": "..."}`

#### Test 2: API Info ✅
```bash
curl http://localhost:8000/
```
**Expected:** API information JSON

#### Test 3: Metrics ✅
```bash
curl http://localhost:8000/metrics
```
**Expected:** Prometheus metrics

## 📝 Testing Agent Management

### Register an Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-first-agent",
    "name": "My First Agent",
    "version": "1.0.0",
    "description": "My test agent",
    "capabilities": ["test", "demo"]
  }'
```

**Expected Response:**
```json
{
  "agent_id": "my-first-agent",
  "api_token": "gml_...",
  "public_key": "did:gml:..."
}
```

### Get Agent Details
```bash
curl http://localhost:8000/api/v1/agents/my-first-agent
```

### List All Agents
```bash
curl http://localhost:8000/api/v1/agents
```

## 🧪 Automated Testing

### Run Python Test Script
```bash
python test_working_examples.py
```

### Run Bash Test Script
```bash
./SIMPLE_WORKING_EXAMPLE.sh
```

## 🔍 Troubleshooting

### Issue: "Failed to register agent"
**Solution:**
1. Check database is running: `docker-compose ps postgres`
2. Check server logs: `tail -f /tmp/gml_server.log`
3. Verify database connection in `.env` file

### Issue: "Connection refused"
**Solution:**
1. Make sure server is running: `ps aux | grep uvicorn`
2. Check port 8000 is free: `lsof -i :8000`
3. Restart server if needed

### Issue: "Database connection error"
**Solution:**
1. Check PostgreSQL is healthy: `docker-compose logs postgres`
2. Verify DATABASE_URL in `.env`
3. Run migrations: `alembic upgrade head`

## 📊 What Each Service Does

### PostgreSQL (Database)
- Stores agents, messages, memories, costs
- **No API key needed** - runs locally

### Redis (Cache & Queue)
- Message queue between agents
- Caching for embeddings
- **No API key needed** - runs locally

### Qdrant (Vector Database)
- Stores vector embeddings for semantic search
- **No API key needed** - runs locally

### OpenAI (Optional)
- Generates embeddings for semantic search
- **API key needed** - only if you want real embeddings
- Without it: system works but embeddings are stubs

## 🎯 Testing Checklist

- [ ] Docker services running
- [ ] API server running on port 8000
- [ ] Health endpoint returns 200
- [ ] Can register an agent
- [ ] Can retrieve agent details
- [ ] Can list agents
- [ ] Can write memory
- [ ] Can search memory (basic, without OpenAI)

## 💡 Pro Tips

1. **Start Simple**: Test health endpoint first
2. **Check Logs**: Always check `/tmp/gml_server.log` for errors
3. **Use API Docs**: Visit http://localhost:8000/api/docs for interactive testing
4. **No OpenAI Needed**: Most features work without OpenAI API key

## 🚀 Next Steps

Once basic testing works:
1. Add OpenAI API key (optional) for better embeddings
2. Test message sending between agents
3. Test memory search with real embeddings
4. Monitor costs and metrics

## 📚 Resources

- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

