#!/bin/bash
# Kill old server and restart

cd "/Volumes/Yatri Cloud/org/gml/project"

echo "Killing old server..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 2

echo "Activating venv and starting server..."
source venv/bin/activate
cd src
uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
