# 🔧 What You Need - GML Infrastructure Setup Guide

## 📋 Overview

This guide explains what external services and APIs you need to run the GML Infrastructure.

## ✅ What's Already Included (No Setup Needed)

### 1. **Docker Services** (Local - No API Keys)
- ✅ **PostgreSQL** - Database (runs locally via Docker)
- ✅ **Redis** - Caching & Pub/Sub (runs locally via Docker)
- ✅ **Qdrant** - Vector Database (runs locally via Docker)
- ✅ **MinIO** - Object Storage (runs locally via Docker)

**Status**: These are already running via `docker-compose.dev.yml` - **NO API KEYS NEEDED**

## 🔑 External Services You MAY Need

### 1. **OpenAI API** (Optional - Only for Embeddings)

**When you need it:**
- When using memory search (semantic search)
- When writing memories (to generate embeddings)

**What you need:**
- OpenAI API Key (starts with `sk-`)
- Model: `text-embedding-3-small` (default, 1536 dimensions)

**How to get it:**
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env` file:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

**Cost:** ~$0.02 per 1M tokens (very cheap for embeddings)

**Alternative:** You can use other embedding services or local models, but you'll need to modify the embedding service.

### 2. **OpenRouter** (NOT NEEDED)

**Status**: ❌ **You don't need OpenRouter** for this system.

OpenRouter is for LLM inference, but this infrastructure focuses on:
- Agent management
- Message routing
- Memory storage
- Cost tracking

If you want to add LLM capabilities later, you can integrate OpenRouter or OpenAI's chat API.

## 🚀 What Works WITHOUT External APIs

### ✅ Fully Working (No API Keys Needed):
1. **Agent Registration** - Register and manage agents
2. **Agent Listing** - List all registered agents
3. **Message Queue** - Send messages between agents (via Redis)
4. **Memory Storage** - Store memories in database
5. **Cost Tracking** - Track costs for operations
6. **Health Monitoring** - Check system health
7. **Metrics** - Prometheus metrics

### ⚠️ Partially Working (Needs OpenAI for Full Functionality):
1. **Memory Search** - Will work but with limited semantic search
2. **Embedding Generation** - Needs OpenAI API key for real embeddings

## 📝 Current Status

### Working Endpoints:
- ✅ `GET /health` - Health check
- ✅ `GET /` - API information
- ✅ `GET /metrics` - Prometheus metrics

### Needs Database Fix:
- ⚠️ `POST /api/v1/agents/register` - Database session issue
- ⚠️ `GET /api/v1/agents/{agent_id}` - Database session issue
- ⚠️ `GET /api/v1/agents` - Database session issue

## 🔧 Quick Setup

### 1. **No External APIs Needed** (Basic Testing):
```bash
# Just start Docker services
docker-compose -f docker-compose.dev.yml up -d

# Start API server
cd src
uvicorn gml.api.main:app --reload
```

### 2. **With OpenAI** (For Embeddings):
```bash
# Add to .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Restart server
```

## 🎯 Testing Guide

### Test 1: Basic Health (No APIs Needed)
```bash
curl http://localhost:8000/health
```

### Test 2: Agent Registration (No APIs Needed)
```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "name": "Test Agent",
    "version": "1.0.0",
    "description": "Test",
    "capabilities": ["test"]
  }'
```

### Test 3: Memory Write (Works without OpenAI, but embeddings will be stubs)
```bash
curl -X POST http://localhost:8000/api/v1/memory/write \
  -H "Content-Type: application/json" \
  -H "X-Agent-ID: test-agent" \
  -d '{
    "conversation_id": "conv-001",
    "content": {"text": "Hello"},
    "memory_type": "episodic",
    "visibility": "all",
    "tags": ["test"]
  }'
```

## 📊 Summary

| Feature | Needs API Key? | Status |
|---------|---------------|--------|
| Agent Management | ❌ No | ⚠️ Needs DB fix |
| Message Queue | ❌ No | ✅ Working |
| Memory Storage | ❌ No | ✅ Working |
| Memory Search | ✅ OpenAI (optional) | ⚠️ Works without, better with |
| Cost Tracking | ❌ No | ✅ Working |
| Health Checks | ❌ No | ✅ Working |

## 🎯 Bottom Line

**You DON'T need:**
- ❌ OpenRouter
- ❌ OpenAI (unless you want semantic search)

**You DO need:**
- ✅ Docker (for local services)
- ✅ Python 3.11+ (already installed)
- ✅ OpenAI API key (optional, only for embeddings)

**Current Issue:**
- Database session handling needs to be fixed
- Once fixed, everything will work without external APIs

