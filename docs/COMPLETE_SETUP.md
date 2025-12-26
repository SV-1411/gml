# Complete Setup Guide

## 1. Environment Variables

### Quick Setup:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
./SETUP_ENV.sh
```

This creates `.env` with all defaults needed to work with docker-compose.

### Or Manual:
```bash
cp .env.example .env
# Edit .env if needed
```

**All defaults work out of the box!** The .env file is configured to match docker-compose.dev.yml.

## 2. Start Services

### Start Docker Services:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

This starts:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Qdrant (port 6333)
- ✅ MinIO (ports 9000, 9001)

### Start Backend:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project"
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
uvicorn src.gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend:
```bash
cd "/Volumes/Yatri Cloud/org/gml/project/frontend"
npm run dev
```

## 3. Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

## 4. Frontend Features

### Dashboard
- Live statistics (agents, memories, files)
- Recent files from MinIO
- System health status
- Auto-refreshes every 30 seconds

### Analytics Page (NEW!)
- Comprehensive system analytics
- Memory statistics and predictions
- Agent activity metrics
- System health monitoring
- Insights and recommendations
- Activity charts

### Memories Page
- Search memories
- Memory statistics
- File storage information
- Storage URLs display

### Agents Page
- Register agents
- View all agents
- Activate/deactivate
- Agent statistics

### Chat Page
- Chat with AI
- Memory integration
- Live thinking animation
- Streaming responses

## 5. All Environment Variables

See `.env.example` for complete list. Key ones:

```bash
# Backend
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gml_db
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
SECRET_KEY=dev-secret-key-change-in-production

# Frontend
VITE_API_URL=http://localhost:8000
```

## 6. Meaningful Data Displayed

### Dashboard:
- Total agents count
- Active agents count
- Total memories count
- Files in storage count and size
- Recent files from MinIO
- System health

### Analytics Page:
- Agent statistics and predictions
- Memory analytics with charts
- File storage analytics
- System health monitoring
- Activity trends
- Insights and recommendations

### Memories Page:
- Memory search results
- Similarity scores
- Storage URLs
- File information
- Memory statistics

All data is **live and auto-updating** for meaningful insights!

