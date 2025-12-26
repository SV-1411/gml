#!/bin/bash
# Complete GML Test with Ollama Models

echo "=========================================="
echo "GML Infrastructure - Complete Test"
echo "With Ollama Models (GPT-OSS 20B & Gemini)"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

# Test 1: Health
echo "1. System Health:"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# Test 2: Register Agent 1 (GPT-OSS)
echo "2. Register Weather Agent (GPT-OSS 20B):"
curl -s -X POST "$BASE_URL/api/v1/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "weather-gpt-oss",
    "name": "Weather Agent (GPT-OSS)",
    "version": "1.0.0",
    "description": "Powered by GPT-OSS 20B",
    "capabilities": ["weather", "llm"]
  }' | python3 -m json.tool
echo ""

# Test 3: Register Agent 2 (Gemini)
echo "3. Register News Agent (Gemini 3 Flash):"
curl -s -X POST "$BASE_URL/api/v1/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "news-gemini",
    "name": "News Agent (Gemini)",
    "version": "1.0.0",
    "description": "Powered by Gemini 3 Flash",
    "capabilities": ["news", "llm"]
  }' | python3 -m json.tool
echo ""

# Test 4: List Agents
echo "4. List All Agents:"
curl -s "$BASE_URL/api/v1/agents" | python3 -m json.tool | head -30
echo ""

# Test 5: Ollama Health
echo "5. Ollama Health:"
curl -s "$BASE_URL/api/v1/ollama/health" | python3 -m json.tool
echo ""

# Test 6: List Ollama Models
echo "6. Available Ollama Models:"
curl -s "$BASE_URL/api/v1/ollama/models" | python3 -m json.tool
echo ""

# Test 7: Test GPT-OSS 20B
echo "7. Test GPT-OSS 20B:"
curl -s -X POST "$BASE_URL/api/v1/ollama/simple" \
  -d "message=What is 2+2? Answer in one word." \
  -d "system_message=You are a math tutor." \
  -d "model=gpt-oss:20b" | python3 -m json.tool
echo ""

# Test 8: Test Gemini 3 Flash
echo "8. Test Gemini 3 Flash:"
curl -s -X POST "$BASE_URL/api/v1/ollama/simple" \
  -d "message=What is 2+2? Answer in one word." \
  -d "system_message=You are a math tutor." \
  -d "model=gemini-3-flash-preview:cloud" | python3 -m json.tool
echo ""

# Test 9: Memory Write
echo "9. Write Memory:"
curl -s -X POST "$BASE_URL/api/v1/memory/write" \
  -H "Content-Type: application/json" \
  -H "X-Agent-ID: weather-gpt-oss" \
  -d '{
    "conversation_id": "conv-ollama-001",
    "content": {"text": "Test memory with Ollama integration"},
    "memory_type": "episodic",
    "visibility": "all",
    "tags": ["ollama", "test"]
  }' | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ Complete Test Finished!"
echo "=========================================="

