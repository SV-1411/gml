# Environment Variables Setup

## Quick Setup

1. **Copy the example file:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project"
   cp .env.example .env
   ```

2. **Edit .env file** (optional - defaults work for development):
   ```bash
   # Most defaults work out of the box, but you can customize:
   nano .env
   ```

3. **For production**, update:
   - `SECRET_KEY` - Generate with: `openssl rand -hex 32`
   - `DATABASE_URL` - Your production database
   - `OPENAI_API_KEY` - If using OpenAI

## Default Values (Works with Docker Compose)

All default values are configured to work with the docker-compose.dev.yml setup:

- **Database:** `postgresql://postgres:postgres@localhost:5432/gml_db`
- **Redis:** `redis://localhost:6379/0`
- **Qdrant:** `http://localhost:6333`
- **MinIO:** `localhost:9000` (Access: minioadmin/minioadmin)

## Required for Backend

The backend uses these environment variables from `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gml_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333

# MinIO (optional - code has fallback)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Security
SECRET_KEY=dev-secret-key-change-in-production
```

## Required for Frontend

The frontend uses:

```bash
VITE_API_URL=http://localhost:8000
```

This is in `frontend/.env` or set in the build process.

## Verify Setup

After setting up .env:

1. **Start services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **Start backend:**
   ```bash
   cd "/Volumes/Yatri Cloud/org/gml/project"
   source venv/bin/activate
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   uvicorn src.gml.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

## All Services Should Be Running

- ✅ PostgreSQL: http://localhost:5432
- ✅ Redis: http://localhost:6379
- ✅ Qdrant: http://localhost:6333
- ✅ MinIO Console: http://localhost:9001
- ✅ MinIO API: http://localhost:9000
- ✅ Backend API: http://localhost:8000
- ✅ Frontend: http://localhost:3000

