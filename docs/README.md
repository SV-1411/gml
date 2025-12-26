# GML Infrastructure

## Overview

Multi-Agent Orchestration Platform for seamless agent communication, coordination, and management. Built with FastAPI, PostgreSQL, and Redis for production-ready multi-agent systems.

## Features

- **Agent Registry & Discovery** - Register, discover, and manage AI agents with unique identifiers and capabilities
- **Async Message Queue** - Inter-agent communication with Redis Pub/Sub and reliable message delivery
- **Shared Memory with Semantic Search** - Persistent memory storage with vector-based semantic search using Qdrant
- **Cost Tracking & Billing** - Comprehensive cost tracking per agent and operation with billing period support
- **Comprehensive Monitoring** - Health checks, Prometheus metrics, and detailed audit logging

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7

### Setup

```bash
git clone <repo>
cd gml-infrastructure
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
docker-compose -f docker-compose.dev.yml up -d
cd src
python -m uvicorn gml.api.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Project Structure

```
gml-infrastructure/
├── src/gml/                  # Main application code
│   ├── api/                  # FastAPI routes and schemas
│   │   ├── routes/           # API endpoint handlers
│   │   └── schemas/          # Pydantic request/response models
│   ├── core/                 # Core configuration and security
│   ├── db/                   # Database models and migrations
│   ├── services/             # Business logic layer
│   ├── cache/                # Redis caching layer
│   ├── workers/              # Background workers
│   └── monitoring/          # Metrics and observability
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/         # Integration tests
│   └── conftest.py           # Test fixtures
├── alembic/                  # Database migrations
├── docs/                     # Documentation
├── k8s/                      # Kubernetes manifests
└── docker-compose.dev.yml    # Development environment
```

## API Endpoints

### Agent Management

- `POST /api/v1/agents/register` - Register a new agent
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `GET /api/v1/agents` - List agents with pagination

### Memory Management

- `POST /api/v1/memory/write` - Write memory to shared storage
- `GET /api/v1/memory/{context_id}` - Retrieve memory by ID
- `POST /api/v1/memory/search` - Semantic search across memories

### Health & Monitoring

- `GET /health` - Basic health check
- `GET /metrics` - Prometheus metrics
- `GET /api/v1/health/detailed` - Detailed service health

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/gml --cov-report=html

# Run specific test suite
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/
pylint src/

# Type checking
mypy src/
```

### Environment Variables

Create a `.env` file in the project root:

```env
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

# Security
SECRET_KEY=your-secret-key-here
```

## Services

The development environment includes:

- **PostgreSQL 15** - Primary database (port 5432)
- **Redis 7** - Caching and message queue (port 6379)
- **Qdrant** - Vector database for semantic search (ports 6333, 6334)
- **MinIO** - S3-compatible object storage (ports 9000, 9001)

## Deployment

### Docker

```bash
# Build production image
docker build -f Dockerfile.dev -t gml-infrastructure:latest .

# Run container
docker run -p 8000:8000 gml-infrastructure:latest
```

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
```

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Database Schema](src/gml/db/DATABASE.md)
- [Migrations Guide](docs/MIGRATIONS.md)
- [API Documentation](http://localhost:8000/api/docs)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
