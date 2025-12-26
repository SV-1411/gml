#!/bin/bash
# Kill old server and restart

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Stopping old server on port 8000..."
PID=$(lsof -ti:8000 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Found process $PID on port 8000, killing it..."
    kill -9 $PID 2>/dev/null
    sleep 2
    echo "✅ Old server stopped"
else
    echo "No server running on port 8000"
fi

echo ""
echo "Clearing Python cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ venv not found!"
    exit 1
fi

echo ""
echo "Starting server..."
echo ""

cd src
exec uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000

