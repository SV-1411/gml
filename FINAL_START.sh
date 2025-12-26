#!/bin/bash
# Final Working Start Script

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Stopping old server..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

echo "Activating virtual environment..."
source venv/bin/activate

echo "Clearing cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "Starting server from src directory..."
echo ""

cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000

