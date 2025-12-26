#!/bin/bash
# Fixed Server Start Script - Sets correct PYTHONPATH

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Stopping any existing server..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ venv not found!"
    exit 1
fi

echo "Clearing Python cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "Starting server from src directory..."
echo ""

# IMPORTANT: Must run from src directory and set PYTHONPATH
cd src
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000

