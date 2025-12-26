# Configuration Module

Centralized configuration management for GML Infrastructure using Pydantic BaseSettings.

## Features

- **Type-Safe**: Full type hints and Pydantic validation
- **Environment Variables**: Automatic loading from `.env` file
- **Singleton Pattern**: Consistent configuration across the application
- **Sensible Defaults**: Works out-of-the-box for local development
- **Security**: Sensitive value masking for safe logging
- **Validation**: Automatic validation of URLs and formats

## Quick Start

```python
from src.gml.core.config import get_settings, settings

# Method 1: Use the pre-initialized instance
print(settings.APP_NAME)

# Method 2: Get the singleton instance
config = get_settings()
print(config.DATABASE_URL)
```

## Configuration Groups

### Application Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_NAME` | str | `gml-infrastructure` | Application name |
| `DEBUG` | bool | `False` | Debug mode flag |
| `ENVIRONMENT` | str | `development` | Environment: development/staging/production |

### Database & Infrastructure

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | str | `postgresql://...` | PostgreSQL connection URL |
| `REDIS_URL` | str | `redis://...` | Redis cache URL |
| `QDRANT_URL` | str | `http://localhost:6333` | Qdrant vector DB URL |
| `QDRANT_API_KEY` | str | None | Qdrant API key (optional) |

### Security & Authentication

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | str | `dev-secret-key...` | Cryptographic secret key |
| `ALGORITHM` | str | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_HOURS` | int | `24` | JWT expiration time |

### AI/ML Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | str | `` | OpenAI API key |
| `EMBEDDING_MODEL` | str | `text-embedding-3-small` | Embedding model name |

### Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | str | `INFO` | Logging level |

## Usage Examples

### Basic Access

```python
from src.gml.core.config import settings

# Access configuration values
app_name = settings.APP_NAME
db_url = settings.DATABASE_URL
debug_mode = settings.DEBUG
```

### Environment Checks

```python
from src.gml.core.config import get_settings

config = get_settings()

if config.is_development:
    print("Running in development mode")

if config.is_production:
    print("Running in production mode")

# Get environment-specific values
pool_size = config.database_pool_size  # 5 in dev, 20 in prod
```

### Safe Logging

```python
from src.gml.core.config import settings
import json

# Mask sensitive values for logging
safe_config = settings.model_dump_safe()
print(json.dumps(safe_config, indent=2))

# Output:
# {
#   "SECRET_KEY": "dev-***ion",
#   "OPENAI_API_KEY": "***",
#   ...
# }
```

### Database Configuration

```python
from sqlalchemy.ext.asyncio import create_async_engine
from src.gml.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.database_pool_size,
    echo=settings.DEBUG
)
```

### Redis Configuration

```python
import redis.asyncio as redis
from src.gml.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)
```

### OpenAI Configuration

```python
from openai import AsyncOpenAI
from src.gml.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def get_embedding(text: str):
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding
```

## Environment Variables

Create a `.env` file in your project root:

```bash
# Application
APP_NAME=my-gml-app
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# AI/ML
OPENAI_API_KEY=sk-your-key-here
EMBEDDING_MODEL=text-embedding-3-small

# Logging
LOG_LEVEL=DEBUG
```

## Validation

The module includes automatic validation:

### Database URL Validation
```python
# Must start with postgresql:// or postgres://
DATABASE_URL=postgresql://localhost/mydb  # ✓ Valid
DATABASE_URL=mysql://localhost/mydb       # ✗ Invalid
```

### Redis URL Validation
```python
# Must start with redis:// or rediss://
REDIS_URL=redis://localhost:6379         # ✓ Valid
REDIS_URL=http://localhost:6379          # ✗ Invalid
```

### Secret Key Warning
```python
# Warns if using default key in production
ENVIRONMENT=production
SECRET_KEY=dev-secret-key-change-in-production  # ⚠ Warning logged
```

### OpenAI Key Format
```python
# Warns if key doesn't start with sk-
OPENAI_API_KEY=sk-proj-abc123...  # ✓ Valid format
OPENAI_API_KEY=invalid-key        # ⚠ Warning logged
```

## Singleton Pattern

The configuration uses `@lru_cache()` to ensure a single instance:

```python
from src.gml.core.config import get_settings

# Both calls return the same instance
config1 = get_settings()
config2 = get_settings()

assert config1 is config2  # True
```

## Testing

Override configuration in tests:

```python
import pytest
from src.gml.core.config import get_settings

def test_with_custom_config(monkeypatch):
    # Override environment variables
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("DEBUG", "true")

    # Clear cache to reload settings
    get_settings.cache_clear()

    # Get new settings with overrides
    config = get_settings()
    assert config.APP_NAME == "test-app"
    assert config.DEBUG is True
```

## Properties

### Computed Properties

- `is_development`: Returns `True` if `ENVIRONMENT == "development"`
- `is_production`: Returns `True` if `ENVIRONMENT == "production"`
- `is_staging`: Returns `True` if `ENVIRONMENT == "staging"`
- `database_pool_size`: Returns 5 for dev, 20 for production
- `log_level_int`: Returns numeric log level for Python logging

### Methods

- `configure_logging()`: Sets up application logging
- `model_dump_safe()`: Returns dict with masked sensitive values

## Best Practices

1. **Never commit secrets**: Always use `.env` file (git-ignored)
2. **Use type hints**: Leverage IDE autocomplete and type checking
3. **Environment-specific logic**: Use `is_development`, `is_production` properties
4. **Safe logging**: Use `model_dump_safe()` when logging configuration
5. **Cache clearing**: Clear `get_settings.cache_clear()` in tests only

## Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Generate secure `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Set valid `OPENAI_API_KEY`
- [ ] Configure production `DATABASE_URL`
- [ ] Configure production `REDIS_URL`
- [ ] Set `LOG_LEVEL=INFO` or `WARNING`
- [ ] Review all default values

## Troubleshooting

### Configuration not loading

```python
# Check if .env file exists
import os
print(os.path.exists('.env'))

# Manually check environment variables
import os
print(os.getenv('APP_NAME'))
```

### Validation errors

```python
# Enable verbose validation errors
from src.gml.core.config import Settings

try:
    config = Settings()
except Exception as e:
    print(e.errors())
```

### Cache issues

```python
# Clear cache in development/testing
from src.gml.core.config import get_settings

get_settings.cache_clear()
config = get_settings()  # Reloads from environment
```
