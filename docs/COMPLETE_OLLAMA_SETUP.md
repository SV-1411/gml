# 🦙 Complete Ollama Setup & Testing Guide

## ✅ What's Integrated

1. **Ollama Service** - `src/gml/services/ollama_service.py`
2. **Ollama API Routes** - `src/gml/api/routes/ollama.py`
3. **Configuration** - Added to `src/gml/core/config.py`
4. **Test Scripts** - Multiple test files

## 🚀 Setup (3 Steps)

### Step 1: Install & Start Ollama
```bash
# Install (if not already installed)
brew install ollama

# Start Ollama
ollama serve
```

### Step 2: Pull GPT-OSS 20B Model
```bash
ollama pull gpt-oss:20b
```

**Note:** This downloads ~40GB. May take 10-30 minutes depending on your connection.

### Step 3: Verify
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Should return list of models
```

## 🧪 Testing

### Test 1: Standalone Test (No Dependencies)
```bash
python test_ollama_standalone.py
```

This test works even if the API server has issues.

### Test 2: Direct Service Test
```bash
python test_ollama_direct.py
```

### Test 3: API Endpoint Test
```bash
python test_ollama_api.py
```

## 📝 Usage Examples

### Python - Simple Chat
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

### Python - Function Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"]
        }
    }
}]

response = await service.chat_with_tools(
    "What's the weather in Berlin?",
    tools=tools
)
```

### HTTP API - Simple Chat
```bash
curl -X POST "http://localhost:8000/api/v1/ollama/simple?message=Hello&system_message=You%20are%20helpful"
```

### HTTP API - Full Chat
```bash
curl -X POST http://localhost:8000/api/v1/ollama/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is AI?"}
    ],
    "model": "gpt-oss:20b"
  }'
```

## ✅ What You Need - FINAL ANSWER

### ❌ You DON'T Need:
- **OpenRouter** - Not required
- **OpenAI API Key** - Not required (Ollama runs locally)
- **External APIs** - Everything local

### ✅ You DO Need:
1. **Ollama installed** - `brew install ollama`
2. **Ollama running** - `ollama serve`
3. **Model pulled** - `ollama pull gpt-oss:20b`

## 🎯 Quick Test

```bash
# 1. Start Ollama
ollama serve

# 2. Pull model (in another terminal)
ollama pull gpt-oss:20b

# 3. Test (in another terminal)
python test_ollama_standalone.py
```

## 📊 API Endpoints

Once server is running:
- `POST /api/v1/ollama/chat` - Full chat completion
- `POST /api/v1/ollama/simple` - Simple chat
- `GET /api/v1/ollama/health` - Health check
- `GET /api/v1/ollama/models` - List models

## 🎉 Summary

- ✅ **Ollama integrated** - Full OpenAI-compatible interface
- ✅ **GPT-OSS 20B ready** - Local LLM inference
- ✅ **Function calling** - Full tool support
- ✅ **No external APIs** - Everything runs locally
- ✅ **Privacy** - All data stays local

## 📚 Files

- **Service**: `src/gml/services/ollama_service.py`
- **Routes**: `src/gml/api/routes/ollama.py`
- **Tests**: `test_ollama_standalone.py`, `test_ollama_direct.py`, `test_ollama_api.py`
- **Docs**: `OLLAMA_SETUP.md`, `FINAL_OLLAMA_GUIDE.md`

## ✅ Status: READY!

Run `python test_ollama_standalone.py` to test Ollama integration!

