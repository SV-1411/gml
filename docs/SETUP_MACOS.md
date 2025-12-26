# macOS Setup Guide - GML Infrastructure

Complete step-by-step setup instructions for macOS (M4 Mac compatible).

## Prerequisites

Ensure you have installed:
- Python 3.11 or higher
- Docker Desktop for Mac
- Git
- Homebrew (optional, for easier package management)

Verify installations:
```bash
python3 --version  # Should be 3.11+
docker --version
git --version
```

---

## Step 1: Create GitHub Repository

### Option A: Create New Repository on GitHub

1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Fill in:
   - Repository name: `gml-infrastructure` (or your preferred name)
   - Description: "Multi-Agent Orchestration Platform"
   - Visibility: Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we'll add these)
4. Click **"Create repository"**
5. Copy the repository URL (e.g., `https://github.com/yourusername/gml-infrastructure.git`)

### Option B: Use Existing Repository

If you already have a repository, note the clone URL.

---

## Step 2: Clone Repository

```bash
# Navigate to your desired directory
cd ~/Projects  # or wherever you keep projects

# Clone the repository
git clone https://github.com/yourusername/gml-infrastructure.git

# Navigate into the project
cd gml-infrastructure
```

---

## Step 3: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Verify venv was created
ls -la venv/
```

---

## Step 4: Activate Virtual Environment

```bash
# Activate the virtual environment
source venv/bin/activate

# Verify activation (your prompt should show (venv))
which python  # Should point to venv/bin/python
```

**Note:** You'll need to activate the venv every time you open a new terminal:
```bash
source venv/bin/activate
```

---

## Step 5: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
pip list | grep -E "(fastapi|sqlalchemy|pytest)"
```

---

## Step 6: Create .env File

```bash
# Create .env file from template (if .env.example exists)
cp .env.example .env

# OR create .env manually
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

# Verify .env was created
cat .env
```

---

## Step 7: Start Docker Services

```bash
# Start all services in detached mode
docker-compose -f docker-compose.dev.yml up -d

# Wait a few seconds for services to start, then check status
docker-compose -f docker-compose.dev.yml ps

# View logs to verify services are healthy
docker-compose -f docker-compose.dev.yml logs --tail=50
```

**Expected output:** All services should show as "Up" and "healthy":
- `gml-postgres` - Up (healthy)
- `gml-redis` - Up (healthy)
- `gml-qdrant` - Up (healthy)
- `gml-minio` - Up (healthy)

**If services aren't healthy, wait 30 seconds and check again:**
```bash
docker-compose -f docker-compose.dev.yml ps
```

---

## Step 8: Initialize Database

```bash
# Verify database is accessible
docker exec gml-postgres pg_isready -U postgres

# Connect to database and verify it exists
docker exec -it gml-postgres psql -U postgres -c "\l" | grep gml_db
```

The database `gml_db` should already exist (created automatically by Docker).

---

## Step 9: Run Database Migrations

```bash
# Make sure you're in the project root directory
pwd  # Should show: .../gml-infrastructure

# Run migrations to create all tables
alembic upgrade head

# Verify migrations ran successfully
alembic current
```

**Expected output:** Should show the latest migration revision.

**If you see errors about database connection:**
- Wait a bit longer for PostgreSQL to be fully ready
- Check Docker logs: `docker-compose -f docker-compose.dev.yml logs postgres`
- Verify DATABASE_URL in .env file

---

## Step 10: Start FastAPI Server

```bash
# Make sure venv is activated
source venv/bin/activate

# Navigate to src directory
cd src

# Start the FastAPI server with auto-reload
python -m uvicorn gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal open** - the server runs in the foreground.

**In a new terminal window/tab**, continue with testing.

---

## Step 11: Test Health Endpoint

```bash
# Test basic health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-..."}

# Test with pretty JSON output
curl -s http://localhost:8000/health | python3 -m json.tool

# Test detailed health check
curl -s http://localhost:8000/api/v1/health/detailed | python3 -m json.tool

# Test root endpoint
curl -s http://localhost:8000/ | python3 -m json.tool
```

**Expected responses:**

**Basic health:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456+00:00"
}
```

**Detailed health:**
```json
{
  "database": {
    "status": "healthy",
    "message": null
  },
  "redis": {
    "status": "healthy",
    "message": null
  },
  "qdrant": {
    "status": "healthy",
    "message": null
  }
}
```

---

## Verification Checklist

Run these commands to verify everything is working:

```bash
# 1. Check Docker services
docker-compose -f docker-compose.dev.yml ps

# 2. Check database connection
docker exec gml-postgres psql -U postgres -d gml_db -c "SELECT version();"

# 3. Check Redis connection
docker exec gml-redis redis-cli ping  # Should return: PONG

# 4. Check Qdrant
curl http://localhost:6333/healthz

# 5. Check FastAPI is running
curl http://localhost:8000/health

# 6. Check API documentation
open http://localhost:8000/api/docs  # Opens in browser
```

---

## Quick Reference Commands

### Start Development Environment
```bash
# Activate venv
source venv/bin/activate

# Start Docker services
docker-compose -f docker-compose.dev.yml up -d

# Start FastAPI server
cd src && python -m uvicorn gml.api.main:app --reload
```

### Stop Services
```bash
# Stop FastAPI server: Press CTRL+C in the terminal running it

# Stop Docker services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (WARNING: Deletes data)
docker-compose -f docker-compose.dev.yml down -v
```

### View Logs
```bash
# Docker logs
docker-compose -f docker-compose.dev.yml logs -f

# Specific service logs
docker-compose -f docker-compose.dev.yml logs -f postgres
docker-compose -f docker-compose.dev.yml logs -f redis
```

### Database Operations
```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1

# Check current migration
alembic current
```

---

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :8000  # FastAPI
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill the process (replace PID with actual process ID)
kill -9 PID
```

### Docker Services Not Starting

```bash
# Check Docker is running
docker ps

# View service logs
docker-compose -f docker-compose.dev.yml logs

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

### Database Connection Errors

```bash
# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test database connection manually
docker exec -it gml-postgres psql -U postgres -d gml_db
```

### Python Import Errors

```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements-dev.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

---

## Next Steps

Once setup is complete:

1. **Explore API Documentation:**
   - Open http://localhost:8000/api/docs in your browser
   - Try the interactive API explorer

2. **Run Tests:**
   ```bash
   pytest tests/ -v
   ```

3. **Register Your First Agent:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/agents/register \
     -H "Content-Type: application/json" \
     -d '{
       "agent_id": "test-agent-001",
       "name": "Test Agent",
       "capabilities": ["test"]
     }'
   ```

4. **Read Documentation:**
   - [README.md](README.md) - Project overview
   - [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
   - [docs/](docs/) - Additional documentation

---

## Success! 🎉

Your GML Infrastructure is now running. The API is available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

