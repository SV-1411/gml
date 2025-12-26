# 🎯 GML Complete Test with Ollama Models

## ✅ Models Integrated

1. **GPT-OSS 20B** - `gpt-oss:20b`
2. **Gemini 3 Flash Preview** - `gemini-3-flash-preview:cloud`

## 🚀 Quick Test

### Test Both Models
```bash
python test_both_models.py
```

### Test Complete GML Workflow
```bash
python test_gml_full_workflow_ollama.py
```

### Test via API
```bash
./test_gml_complete_ollama.sh
```

## 📝 Usage Examples

### Use GPT-OSS 20B
```python
from src.gml.services.ollama_service import OllamaService

service = OllamaService(model="gpt-oss:20b")
response = await service.simple_chat("Hello!")
```

### Use Gemini 3 Flash
```python
service = OllamaService(model="gemini-3-flash-preview:cloud")
response = await service.simple_chat("Hello!")
```

### Via HTTP API
```bash
# GPT-OSS 20B
curl -X POST "http://localhost:8000/api/v1/ollama/simple?message=Hello&model=gpt-oss:20b"

# Gemini 3 Flash
curl -X POST "http://localhost:8000/api/v1/ollama/simple?message=Hello&model=gemini-3-flash-preview:cloud"
```

## ✅ Complete GML Workflow

1. **Register Agents** - Agents that use Ollama
2. **Agent Communication** - Messages between agents
3. **Ollama Reasoning** - Agents use Ollama for decision making
4. **Memory Storage** - Store Ollama-generated content
5. **Cost Tracking** - Track Ollama operation costs
6. **Multi-Model** - Use different models for different tasks

## 🎉 Status: READY!

Both models integrated and tested!

