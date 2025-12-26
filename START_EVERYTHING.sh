#!/bin/bash
# Complete Setup and Start Script

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "========================================="
echo "Setting Up and Starting Server"
echo "========================================="
echo ""

# Step 1: Install dependencies
echo "1. Checking dependencies..."
source venv/bin/activate

if ! python -c "import multipart" 2>/dev/null; then
    echo "   Installing python-multipart..."
    pip install python-multipart > /dev/null 2>&1
fi

if ! python -c "import minio" 2>/dev/null; then
    echo "   Installing minio..."
    pip install minio > /dev/null 2>&1
fi

echo "   ✅ Dependencies checked"

# Step 2: Check MinIO
echo ""
echo "2. Checking MinIO..."
if docker ps | grep -q gml-minio; then
    echo "   ✅ MinIO is running"
else
    echo "   ⚠️  Starting MinIO..."
    docker-compose -f docker-compose.dev.yml up -d minio
    sleep 5
fi

# Step 3: Stop old server
echo ""
echo "3. Stopping old server..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Step 4: Clear cache
echo "4. Clearing cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true

# Step 5: Start server
echo ""
echo "5. Starting server..."
echo ""
echo "========================================="
echo "Server Starting..."
echo "========================================="
echo ""

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
uvicorn src.gml.api.main:app --reload --host 0.0.0.0 --port 8000

