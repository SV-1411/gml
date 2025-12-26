#!/bin/bash
# Run this to start server correctly

cd "/Volumes/Yatri Cloud/org/gml/project"

# Kill old server
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

# Activate venv
source venv/bin/activate

# Clear cache
find src -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true

# Go to src directory and start server
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
