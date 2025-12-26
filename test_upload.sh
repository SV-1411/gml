#!/bin/bash
# Test Storage Upload Endpoint

echo "========================================="
echo "Testing Storage Upload Endpoint"
echo "========================================="
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Server is not running on http://localhost:8000"
    echo "Please start the server first:"
    echo "  cd src"
    echo "  uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Check if route exists in API docs
echo "Checking if route is registered..."
if curl -s http://localhost:8000/api/openapi.json | grep -q "storage/upload"; then
    echo "✅ Route found in API docs"
else
    echo "❌ Route NOT found in API docs"
    echo ""
    echo "The server needs to be restarted to load the storage routes!"
    echo "Run: ./restart_server.sh"
    exit 1
fi

echo ""
echo "Testing upload endpoint..."
echo ""

# Create test file
echo "This is a test file for upload" > /tmp/test_upload.txt

# Test upload
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST http://localhost:8000/api/v1/storage/upload \
    -F "file=@/tmp/test_upload.txt" \
    -F "bucket=uploads")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "HTTP Status: $HTTP_STATUS"
echo ""

if [ "$HTTP_STATUS" = "201" ]; then
    echo "✅ Upload successful!"
    echo ""
    echo "Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "❌ Upload failed"
    echo ""
    echo "Response:"
    echo "$BODY"
fi

# Cleanup
rm -f /tmp/test_upload.txt

echo ""
echo "========================================="

