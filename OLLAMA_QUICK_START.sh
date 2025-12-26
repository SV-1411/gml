#!/bin/bash
# Quick Start Script for Ollama Integration

echo "=========================================="
echo "Ollama + GPT-OSS 20B - Quick Start"
echo "=========================================="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed!"
    echo ""
    echo "Install Ollama:"
    echo "  macOS: brew install ollama"
    echo "  Or visit: https://ollama.ai"
    exit 1
fi

echo "✅ Ollama is installed"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running!"
    echo ""
    echo "Start Ollama in another terminal:"
    echo "  ollama serve"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Check if model is available
MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print(' '.join([m['name'] for m in data.get('models', [])]))" 2>/dev/null)

if [[ "$MODELS" == *"gpt-oss:20b"* ]]; then
    echo "✅ GPT-OSS 20B model is available"
else
    echo "⚠️  GPT-OSS 20B model not found"
    echo ""
    echo "Pull the model:"
    echo "  ollama pull gpt-oss:20b"
    echo ""
    echo "This will download ~40GB, may take a while."
    exit 1
fi

echo ""
echo "=========================================="
echo "Testing GML Integration"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

# Test 1: Health
echo "1. Ollama Health Check:"
curl -s "$BASE_URL/api/v1/ollama/health" | python3 -m json.tool
echo ""

# Test 2: List Models
echo "2. Available Models:"
curl -s "$BASE_URL/api/v1/ollama/models" | python3 -m json.tool
echo ""

# Test 3: Simple Chat
echo "3. Simple Chat Test:"
curl -s -X POST "$BASE_URL/api/v1/ollama/simple" \
  -d "message=Say hello in one sentence." \
  -d "system_message=You are a helpful assistant." | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test full integration: python test_ollama_integration.py"
echo "  2. Test API endpoints: python test_ollama_api.py"
echo "  3. View API docs: http://localhost:8000/api/docs"
echo ""

