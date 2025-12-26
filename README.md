# GML Infrastructure

A multi-agent orchestration platform built with FastAPI, React, and modern infrastructure services. This project provides a complete infrastructure for managing AI agents, semantic memory, and vector embeddings.

## Features

- 🤖 **Multi-Agent Management**: Register, manage, and orchestrate AI agents
- 🧠 **Semantic Memory**: Store and search memories with vector embeddings
- 💬 **Chat Interface**: Interactive chat interface with streaming responses
- 📊 **Analytics Dashboard**: Real-time system analytics and monitoring
- 🔍 **Vector Search**: Advanced semantic search using Qdrant
- 💾 **File Storage**: Object storage with MinIO
- 🚀 **FastAPI Backend**: High-performance async API
- ⚛️ **React Frontend**: Modern UI with TypeScript and Tailwind CSS

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database with async support
- **Redis** - Caching and session management
- **Qdrant** - Vector database for embeddings
- **MinIO** - Object storage
- **SQLAlchemy** - Async ORM
- **Alembic** - Database migrations
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **TanStack Query** - Data fetching
- **Axios** - HTTP client

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** (Python 3.13+ recommended)
- **Node.js 18+** and npm
- **Docker** and **Docker Compose**
- **Git**

Verify installations:
```bash
python3 --version  # Should be 3.11+
node --version     # Should be 18+
docker --version
docker-compose --version
git --version
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/GIGZs-Marketplace/dev-gml.git
cd dev-gml
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy example (if available) or create manually
# The application has sensible defaults, but you can customize:
```

Minimal `.env` configuration:
```bash
# Application
APP_NAME=gml-infrastructure
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database (matches docker-compose defaults)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/gml_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=uploads

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# AI/ML (optional)
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama
OLLAMA_MODEL=gpt-oss:20b
USE_OLLAMA=true

# Frontend
VITE_API_URL=http://localhost:8000
```

> **Note**: For production, generate a secure `SECRET_KEY` using: `openssl rand -hex 32`

### 4. Start Docker Services

The project uses Docker Compose to run infrastructure services:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This starts:
- ✅ **PostgreSQL** on port 5432
- ✅ **Redis** on port 6379
- ✅ **Qdrant** on port 6333
- ✅ **MinIO** on ports 9000 (API) and 9001 (Console)

Verify services are running:
```bash
docker-compose -f docker-compose.dev.yml ps
```

### 5. Run Database Migrations

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Run migrations
alembic upgrade head
```

### 6. Start Backend Server

```bash
# Activate virtual environment (if not already)
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Start server
uvicorn src.gml.api.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 7. Start Frontend

Open a new terminal:

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

The frontend will be available at:
- **Frontend**: http://localhost:3000 (or the port shown in terminal)

## Access Points

Once everything is running:

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **MinIO Console**: http://localhost:9001
  - Username: `minioadmin`
  - Password: `minioadmin`

## Project Structure

```
dev-gml/
├── src/
│   └── gml/
│       ├── api/              # FastAPI application
│       │   ├── main.py       # Application entry point
│       │   ├── middleware.py # Middleware configuration
│       │   ├── routes/       # API route handlers
│       │   └── schemas/      # Pydantic schemas
│       ├── core/             # Core configuration
│       │   ├── config.py     # Settings management
│       │   └── security.py   # Security utilities
│       ├── db/               # Database layer
│       │   ├── database.py   # Database connection
│       │   └── models.py     # SQLAlchemy models
│       ├── services/         # Business logic
│       ├── cache/            # Redis cache
│       ├── monitoring/       # Metrics and monitoring
│       └── workers/          # Background workers
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API clients
│   │   └── contexts/         # React contexts
│   ├── package.json
│   └── vite.config.ts
├── alembic/                  # Database migrations
├── tests/                    # Test suite
├── docs/                     # Documentation
├── docker-compose.dev.yml    # Docker Compose config
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/gml

# Run specific test file
pytest tests/unit/test_agent_service.py -v
```

### Code Formatting

```bash
# Format code with Black
black src/

# Sort imports with isort
isort src/

# Lint with pylint
pylint src/
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

## Environment Variables Reference

### Required for Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/gml_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `QDRANT_URL` | Qdrant endpoint | `http://localhost:6333` |
| `SECRET_KEY` | Secret key for cryptography | `dev-secret-key-change-in-production` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `MINIO_ENDPOINT` | MinIO endpoint | `localhost:9000` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OLLAMA_BASE_URL` | Ollama API base URL | `http://localhost:11434/v1` |
| `USE_OLLAMA` | Use Ollama instead of OpenAI | `true` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

See `src/gml/core/config.py` for complete configuration options.

## Troubleshooting

### Services Not Starting

If Docker services fail to start:
```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs

# Restart services
docker-compose -f docker-compose.dev.yml restart
```

### Database Connection Issues

Ensure PostgreSQL is running:
```bash
docker-compose -f docker-compose.dev.yml ps postgres
```

Check connection:
```bash
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d gml_db
```

### Port Already in Use

If ports are already in use, you can modify ports in `docker-compose.dev.yml` or stop the conflicting service.

### Frontend Build Issues

Clear node modules and reinstall:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## Documentation

Additional documentation is available in the `docs/` directory:

- [Complete Setup Guide](docs/COMPLETE_SETUP.md)
- [Project Documentation](docs/PROJECT_DOCUMENTATION.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)
- [API Documentation](http://localhost:8000/api/docs) (when server is running)

## Credits

**Developed by:** Yatharth Chauhan  
**Contact:** contact@yatharthchauhan.me

## License

This project is private and proprietary.

## Support

For issues and questions, please open an issue on GitHub or contact the development team.

---

**Happy Coding! 🚀**

