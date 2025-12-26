#!/bin/bash
# Simple Working Examples - GML Infrastructure API

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "GML Infrastructure - Simple Working Examples"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "1. Health Check:"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# Test 2: Root Endpoint
echo "2. API Info:"
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""

# Test 3: Register Agent
echo "3. Register Agent:"
curl -s -X POST "$BASE_URL/api/v1/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "demo-agent",
    "name": "Demo Agent",
    "version": "1.0.0",
    "description": "A demo agent",
    "capabilities": ["demo"]
  }' | python3 -m json.tool
echo ""

# Test 4: Get Agent
echo "4. Get Agent:"
curl -s "$BASE_URL/api/v1/agents/demo-agent" | python3 -m json.tool
echo ""

# Test 5: List Agents
echo "5. List Agents:"
curl -s "$BASE_URL/api/v1/agents" | python3 -m json.tool | head -20
echo ""

echo "=========================================="
echo "✅ Examples Complete!"
echo "=========================================="

