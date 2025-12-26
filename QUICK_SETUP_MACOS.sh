#!/bin/bash
# GML Infrastructure - Quick Setup Script for macOS
# Copy and paste these commands in sequence

set -e  # Exit on error

echo "🚀 GML Infrastructure - macOS Setup"
echo "===================================="
echo ""

# Step 1: Create GitHub Repository (Manual)
echo "📝 Step 1: Create GitHub Repository"
echo "   → Go to https://github.com/new"
echo "   → Create repository: gml-infrastructure"
echo "   → DO NOT initialize with README"
echo "   → Copy the repository URL"
echo ""
read -p "Press Enter after creating the repository and copying the URL..."
echo ""

# Step 2: Clone Repository
echo "📥 Step 2: Cloning Repository"
read -p "Enter your GitHub repository URL: " REPO_URL
cd ~/Projects 2>/dev/null || cd ~
git clone "$REPO_URL" gml-infrastructure
cd gml-infrastructure
echo "✅ Repository cloned"
echo ""

# Step 3: Create Python Virtual Environment
echo "🐍 Step 3: Creating Python Virtual Environment"
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Step 4: Activate Virtual Environment
echo "🔌 Step 4: Activating Virtual Environment"
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Step 5: Install Dependencies
echo "📦 Step 5: Installing Dependencies"
pip install --upgrade pip
pip install -r requirements-dev.txt
echo "✅ Dependencies installed"
echo ""

# Step 6: Create .env File
echo "⚙️  Step 6: Creating .env File"
cat > .env << 'EOF'
# Application
ENVIRONMENT=development
DEBUG=true
APP_NAME=gml-infrastructure

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gml_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# AI/ML (optional for now)
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small

# Logging
LOG_LEVEL=INFO
EOF
echo "✅ .env file created"
echo ""

# Step 7: Start Docker Services
echo "🐳 Step 7: Starting Docker Services"
docker-compose -f docker-compose.dev.yml up -d
echo "⏳ Waiting for services to start..."
sleep 10
docker-compose -f docker-compose.dev.yml ps
echo "✅ Docker services started"
echo ""

# Step 8: Initialize Database
echo "🗄️  Step 8: Verifying Database"
docker exec gml-postgres pg_isready -U postgres
echo "✅ Database is ready"
echo ""

# Step 9: Run Migrations
echo "🔄 Step 9: Running Database Migrations"
alembic upgrade head
echo "✅ Migrations completed"
echo ""

# Step 10: Start FastAPI Server (in background)
echo "🚀 Step 10: Starting FastAPI Server"
cd src
python -m uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
cd ..
sleep 5
echo "✅ FastAPI server started (PID: $SERVER_PID)"
echo ""

# Step 11: Test Health Endpoint
echo "🏥 Step 11: Testing Health Endpoint"
sleep 2
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""
echo "✅ Health check passed!"
echo ""

echo "===================================="
echo "🎉 Setup Complete!"
echo "===================================="
echo ""
echo "API is running at: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
echo ""
echo "To stop the server: kill $SERVER_PID"
echo "To stop Docker: docker-compose -f docker-compose.dev.yml down"
echo ""

