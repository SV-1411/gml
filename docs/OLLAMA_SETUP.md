# 🦙 Ollama Integration - GPT-OSS 20B Setup Guide

## 🎯 What You Need

### ✅ Required:
1. **Ollama installed** - https://ollama.ai
2. **GPT-OSS 20B model** - Pulled via Ollama
3. **Ollama running** - `ollama serve`

### ❌ You DON'T Need:
- OpenAI API key (Ollama runs locally)
- External APIs
- Internet connection (after model is pulled)

## 🚀 Quick Setup

### Step 1: Install Ollama
```bash
# macOS
brew install ollama

# Or download from https://ollama.ai
```

### Step 2: Start Ollama
```bash
ollama serve
```

### Step 3: Pull GPT-OSS 20B Model
```bash
ollama pull gpt-oss:20b
```

This will download the model (may take a while, ~40GB).

### Step 4: Verify Ollama is Running
```bash
curl http://localhost:11434/api/tags
```

Should return list of available models.

## 🧪 Testing

### Test 1: Direct Ollama Test
```bash
ollama run gpt-oss:20b "Hello, what is AI?"
```

### Test 2: Python Integration Test
```bash
python test_ollama_integration.py
```

### Test 3: API Endpoint Test
```bash
python test_ollama_api.py
```

## 📝 API Usage Examples

### Simple Chat via API
```bash
curl -X POST http://localhost:8000/api/v1/ollama/simple \
  -d "message=What is AI?" \
  -d "system_message=You are a helpful assistant"
```

### Full Chat Completion
```bash
curl -X POST http://localhost:8000/api/v1/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain MXFP4 quantization"}
    ],
    "model": "gpt-oss:20b",
    "temperature": 0.7
  }'
```

### Check Health
```bash
curl http://localhost:8000/api/v1/ollama/health
```

### List Models
```bash
curl http://localhost:8000/api/v1/ollama/models
```

## 🐍 Python Code Examples

### Example 1: Simple Chat
```python
from src.gml.services.ollama_service import OllamaService

async def main():
    service = OllamaService()
    response = await service.simple_chat(
        "Explain what MXFP4 quantization is."
    )
    print(response)

import asyncio
asyncio.run(main())
```

### Example 2: Chat with System Message
```python
from src.gml.services.ollama_service import OllamaService

async def main():
    service = OllamaService()
    response = await service.simple_chat(
        user_message="What is 2+2?",
        system_message="You are a helpful math tutor."
    )
    print(response)

import asyncio
asyncio.run(main())
```

### Example 3: Function Calling
```python
from src.gml.services.ollama_service import OllamaService

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"}
                },
                "required": ["city"]
            }
        }
    }
]

async def main():
    service = OllamaService()
    response = await service.chat_with_tools(
        "What's the weather in Berlin?",
        tools=tools
    )
    print(response.choices[0].message)

import asyncio
asyncio.run(main())
```

## 🔧 Configuration

### Environment Variables (Optional)
Add to `.env`:
```bash
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama
OLLAMA_MODEL=gpt-oss:20b
USE_OLLAMA=true
```

### Default Settings
- **Base URL**: `http://localhost:11434/v1`
- **API Key**: `ollama` (dummy key)
- **Model**: `gpt-oss:20b`
- **Timeout**: 120 seconds

## 📊 Integration with GML Agents

### Register Agent with Ollama
```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "ollama-agent",
    "name": "Ollama Agent",
    "version": "1.0.0",
    "description": "Agent powered by GPT-OSS 20B",
    "capabilities": ["llm", "chat", "reasoning"]
  }'
```

### Use Ollama in Agent Workflow
```python
from src.gml.services.ollama_service import get_ollama_service

async def agent_process_message(message: str):
    ollama = await get_ollama_service()
    response = await ollama.simple_chat(
        user_message=message,
        system_message="You are an AI agent in the GML infrastructure."
    )
    return response
```

## ✅ Verification Checklist

- [ ] Ollama installed
- [ ] Ollama running (`ollama serve`)
- [ ] Model pulled (`ollama pull gpt-oss:20b`)
- [ ] Health check passes
- [ ] Simple chat works
- [ ] API endpoints respond
- [ ] Integration test passes

## 🎉 Status

Once setup is complete:
- ✅ Local LLM inference (no API costs!)
- ✅ OpenAI-compatible interface
- ✅ Function calling support
- ✅ Integrated with GML infrastructure
- ✅ Full privacy (runs locally)

## 📚 Resources

- **Ollama Docs**: https://ollama.ai/docs
- **GPT-OSS**: https://github.com/gpt-oss
- **API Docs**: http://localhost:8000/api/docs

