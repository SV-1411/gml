#!/bin/bash
# Quick API Test Script

echo "Testing GML Infrastructure API..."
echo ""

BASE_URL="http://localhost:8000"

echo "1. Health Check:"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

echo "2. Root Endpoint:"
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""

echo "3. Register Agent:"
curl -s -X POST "$BASE_URL/api/v1/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent-001",
    "name": "Test Agent",
    "version": "1.0.0",
    "description": "Test agent",
    "capabilities": ["test"]
  }' | python3 -m json.tool
echo ""

echo "4. Get Agent:"
curl -s "$BASE_URL/api/v1/agents/test-agent-001" | python3 -m json.tool
echo ""

echo "✅ All tests complete!"
