#!/bin/bash
# Simple Server Restart Script

echo "Stopping server..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

echo "Clearing cache..."
cd "/Volumes/Yatri Cloud/org/gml/project"
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find src -name "*.pyc" -delete 2>/dev/null || true

echo "Starting server..."
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000

