#!/bin/bash
# Start Server Script - Handles uvicorn not in PATH

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Starting server..."
echo ""

# Try different methods to run uvicorn
cd src

# Method 1: Try python3 -m uvicorn (works if uvicorn is installed)
if python3 -m uvicorn --version > /dev/null 2>&1; then
    echo "Using: python3 -m uvicorn"
    exec python3 -m uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
# Method 2: Try with python -m
elif python -m uvicorn --version > /dev/null 2>&1; then
    echo "Using: python -m uvicorn"
    exec python -m uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
# Method 3: Try activating venv first
elif [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
    exec uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
elif [ -d "../.venv" ]; then
    echo "Activating virtual environment..."
    source ../.venv/bin/activate
    exec uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
else
    echo "❌ uvicorn not found!"
    echo ""
    echo "Please install dependencies first:"
    echo "  pip install -r requirements.txt"
    echo ""
    echo "Or install uvicorn:"
    echo "  pip install uvicorn[standard]"
    echo ""
    echo "Then try:"
    echo "  python3 -m uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi
