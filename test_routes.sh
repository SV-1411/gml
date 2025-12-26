#!/bin/bash
# Test Backend Routes

echo "========================================="
echo "Testing Backend Routes"
echo "========================================="
echo ""

BASE_URL="http://localhost:8000"

echo "1. Testing health endpoint..."
curl -s "$BASE_URL/health" | head -1
echo ""
echo ""

echo "2. Testing storage upload endpoint..."
curl -s -X POST "$BASE_URL/api/v1/storage/upload" \
  -F "file=@/dev/null" \
  -F "bucket=uploads" 2>&1 | head -5
echo ""
echo ""

echo "3. Testing agent status endpoint..."
curl -s -X PATCH "$BASE_URL/api/v1/agents/test-agent/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}' 2>&1 | head -5
echo ""
echo ""

echo "4. Checking API docs..."
curl -s "$BASE_URL/api/openapi.json" | grep -o '"\/api\/v1\/storage[^"]*"' | head -3
echo ""

echo "========================================="
echo "Test Complete"
echo "========================================="

