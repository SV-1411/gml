#!/bin/bash
# Restart Backend Server Script

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "========================================="
echo "Restarting Backend Server"
echo "========================================="
echo ""

# Check if server is running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Server is running on port 8000"
    echo "Stopping server..."
    
    # Try to stop gracefully
    PID=$(lsof -ti:8000)
    kill $PID 2>/dev/null
    sleep 2
    
    # Force kill if still running
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo "Force stopping server..."
        kill -9 $(lsof -ti:8000) 2>/dev/null
        sleep 1
    fi
    
    echo "✅ Server stopped"
else
    echo "No server running on port 8000"
fi

echo ""
echo "Clearing Python cache..."
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true
echo "✅ Cache cleared"

echo ""
echo "Starting server..."
echo ""
echo "========================================="
echo "Starting uvicorn server..."
echo "========================================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd src
exec uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000

