#!/bin/bash
# Quick Start Script - Activates venv and starts server

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ venv/bin/activate not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting server..."
echo ""

cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000

