#!/bin/bash
# Check Server Status and Routes

echo "========================================="
echo "Server Status Check"
echo "========================================="
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Server is NOT running on port 8000"
    echo ""
    echo "Start the server with:"
    echo "  cd src"
    echo "  uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Server is running on port 8000"
echo ""

# Check available routes
echo "Checking available routes..."
ROUTES=$(curl -s http://localhost:8000/api/openapi.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
paths = [p for p in data.get('paths', {}).keys() if '/api/v1' in p]
for p in sorted(paths):
    print(p)
" 2>/dev/null)

echo "Available /api/v1 routes:"
echo "$ROUTES" | while read route; do
    echo "  - $route"
done

echo ""

# Check specifically for storage routes
if echo "$ROUTES" | grep -q "storage"; then
    echo "✅ Storage routes are loaded!"
    echo ""
    echo "Storage routes found:"
    echo "$ROUTES" | grep "storage" | while read route; do
        echo "  ✅ $route"
    done
else
    echo "❌ Storage routes are NOT loaded!"
    echo ""
    echo "========================================="
    echo "ACTION REQUIRED: RESTART SERVER"
    echo "========================================="
    echo ""
    echo "The storage route code exists but the server hasn't loaded it."
    echo ""
    echo "To fix:"
    echo "1. Stop the server (Ctrl+C in terminal running uvicorn)"
    echo "2. Restart it:"
    echo "   cd src"
    echo "   uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    echo "3. Look for this message when server starts:"
    echo "   INFO: Storage router registered at /api/v1/storage"
    echo ""
fi

echo ""
echo "========================================="

