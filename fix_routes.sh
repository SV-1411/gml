#!/bin/bash
# Fix Backend Routes - Complete Setup Script

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "========================================="
echo "Fixing Backend Routes"
echo "========================================="
echo ""

echo "1. Clearing Python cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true
echo "   ✅ Cache cleared"
echo ""

echo "2. Installing dependencies..."
pip install minio > /dev/null 2>&1 && echo "   ✅ MinIO installed" || echo "   ⚠️  MinIO installation skipped (may already be installed)"
echo ""

echo "3. Verifying route files..."
if [ -f "src/gml/api/routes/storage.py" ]; then
    echo "   ✅ storage.py exists"
else
    echo "   ❌ storage.py NOT FOUND"
    exit 1
fi

if [ -f "src/gml/api/routes/agents.py" ]; then
    echo "   ✅ agents.py exists"
else
    echo "   ❌ agents.py NOT FOUND"
    exit 1
fi
echo ""

echo "4. Testing route imports..."
cd src
python3 -c "
try:
    from gml.api.routes import storage_router, agents_router
    print('   ✅ Routes import successfully')
except Exception as e:
    print(f'   ❌ Import error: {e}')
    exit(1)
" || {
    echo "   ❌ Route import failed!"
    exit 1
}
echo ""

echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Stop your current server (Ctrl+C)"
echo "2. Start the server:"
echo "   cd src"
echo "   uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "3. Verify routes at: http://localhost:8000/api/docs"
echo "   - Look for 'storage' section"
echo "   - Look for 'agents' section with PATCH method"
echo ""

