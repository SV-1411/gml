# GML Infrastructure - Project Structure

## Current Structure (Corrected)

```
gml-infrastructure/
├── src/gml/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── middleware.py              # [TO CREATE] Extract middleware from main.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py              # Agent management endpoints
│   │   │   ├── messages.py            # [TO CREATE] Message endpoints
│   │   │   ├── memory.py              # Memory management endpoints
│   │   │   └── health.py              # Health check and metrics
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── agents.py              # Agent Pydantic schemas
│   │       ├── messages.py            # Message Pydantic schemas
│   │       └── memory.py              # Memory Pydantic schemas
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                  # Application configuration
│   │   ├── security.py                # Security utilities (JWT, keys, etc.)
│   │   └── constants.py               # [TO CREATE] Application constants
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py                # Database connection and session management
│   │   └── models.py                  # SQLAlchemy ORM models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_service.py           # Agent business logic
│   │   ├── message_service.py         # Message business logic
│   │   ├── memory_service.py          # [TO CREATE] Memory business logic
│   │   ├── cost_service.py            # Cost tracking logic
│   │   └── exceptions.py              # Custom service exceptions
│   ├── monitoring/
│   │   ├── __init__.py
│   │   └── metrics.py                 # Prometheus metrics collection
│   ├── cache/
│   │   └── __init__.py                # Redis caching utilities (future)
│   ├── utils/
│   │   └── __init__.py                # General utilities (future)
│   └── workers/
│       └── __init__.py                # Background workers (future)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest configuration and fixtures
│   ├── fixtures/
│   │   └── __init__.py                # Test fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   └── test_agent_service.py      # Unit tests for services
│   └── integration/
│       ├── __init__.py
│       └── test_agent_endpoints.py    # Integration tests for API
│
├── alembic/                           # Database migrations
│   ├── env.py                         # Alembic environment configuration
│   ├── script.py.mako                 # Migration template
│   ├── versions/                      # Migration files
│   └── README.md
│
├── docs/                              # Documentation
│   ├── README.md
│   ├── architecture.md                # System architecture
│   └── MIGRATIONS.md                  # Migration guide
│
├── k8s/                               # Kubernetes manifests
│   ├── deployment.yaml
│   ├── configmap.yaml
│   ├── hpa.yaml
│   └── worker-deployment.yaml
│
├── monitoring/                        # Monitoring configuration
│   └── prometheus.yml                 # Prometheus configuration
│
├── examples/                         # Example usage scripts
│   ├── config_usage.py
│   ├── database_usage.py
│   └── security_usage.py
│
├── .pre-commit-config.yaml           # Pre-commit hooks configuration
├── .env.example                      # [TO CREATE] Environment variables template
├── alembic.ini                       # Alembic configuration
├── docker-compose.dev.yml            # Docker Compose for development
├── Dockerfile.dev                    # Dockerfile for development
├── Makefile                          # Make commands
├── pyproject.toml                    # Python project configuration
├── pytest.ini                        # Pytest configuration
├── requirements.txt                  # Production dependencies
├── requirements-dev.txt              # Development dependencies
├── README.md                         # Project README
├── CONTRIBUTING.md                   # Contribution guidelines
├── SETUP_MACOS.md                    # macOS setup guide
└── ALEMBIC_SETUP.md                  # Alembic setup guide
```

## Missing Files to Create

### 1. `src/gml/api/middleware.py`
Extract middleware from `main.py` for better organization.

### 2. `src/gml/api/routes/messages.py`
Message endpoints (currently missing).

### 3. `src/gml/services/memory_service.py`
Memory business logic service.

### 4. `src/gml/core/constants.py`
Application-wide constants.

### 5. `.env.example`
Environment variables template.

## Notes

- **Migrations**: Database migrations are in `alembic/versions/`, not `src/gml/db/migrations/`
- **Schemas**: Pydantic schemas are in `src/gml/api/schemas/` (should be included in structure)
- **Exceptions**: Service exceptions are in `src/gml/services/exceptions.py` (should be included)
- **Documentation**: Additional docs in `src/gml/core/`, `src/gml/db/` subdirectories

## Recommended Actions

1. Extract middleware from `main.py` to `middleware.py`
2. Create missing service files
3. Create `.env.example` template
4. Create `constants.py` for shared constants
5. Create `messages.py` route if needed

