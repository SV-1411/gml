# Database Module

Async SQLAlchemy database connectivity for GML Infrastructure using PostgreSQL with asyncpg driver.

## Features

- **Async Engine**: PostgreSQL connection with asyncpg
- **Connection Pooling**: Configurable pool with health checks
- **Session Management**: FastAPI dependency injection
- **Declarative Base**: ORM model foundation
- **Health Checks**: Database connectivity verification
- **Auto-initialization**: Table creation on startup
- **Cleanup**: Proper connection disposal
- **Debug Logging**: SQL query logging in debug mode
- **Type Safety**: Full type hints for all operations

## Quick Start

### 1. Import Components

```python
from src.gml.db import (
    Base,
    get_db,
    init_db,
    close_db,
    health_check,
    AsyncSessionLocal,
    DatabaseSession,
)
```

### 2. Define Models

```python
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
```

### 3. Initialize Database

```python
import asyncio

async def setup():
    await init_db()  # Creates all tables

asyncio.run(setup())
```

### 4. Use in FastAPI

```python
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

## Core Components

### AsyncEngine

The database engine manages connections and pooling.

```python
from src.gml.db import engine

# Engine is pre-configured with:
# - Connection pooling (5 dev, 20 prod)
# - Pool pre-ping for health checks
# - Connection recycling (1 hour)
# - Debug logging when DEBUG=True
```

**Configuration (automatic from settings):**
- `pool_size`: 5 (development) or 20 (production)
- `max_overflow`: 10 additional connections
- `pool_timeout`: 30 seconds
- `pool_recycle`: 3600 seconds (1 hour)
- `pool_pre_ping`: True
- `echo`: Matches DEBUG setting

### AsyncSessionLocal

Session factory for creating database sessions.

```python
from src.gml.db import AsyncSessionLocal

async def my_function():
    async with AsyncSessionLocal() as session:
        # Use session
        result = await session.execute(select(User))
        users = result.scalars().all()
```

**Session Configuration:**
- `expire_on_commit=False`: Objects remain accessible after commit
- `autocommit=False`: Manual commit required
- `autoflush=False`: Manual flush required

### Base

Declarative base for ORM models.

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from src.gml.db import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

## FastAPI Integration

### Dependency Injection

Use `get_db()` for automatic session management.

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.gml.db import get_db

@app.post("/users")
async def create_user(
    email: str,
    name: str,
    db: AsyncSession = Depends(get_db)
):
    user = User(email=email, name=name)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
```

**Benefits:**
- Automatic session creation
- Automatic commit on success
- Automatic rollback on error
- Automatic session cleanup
- No manual session management

### Application Lifecycle

```python
from fastapi import FastAPI
from src.gml.db import init_db, close_db

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

@app.on_event("shutdown")
async def shutdown():
    await close_db()
```

### Health Check Endpoint

```python
from fastapi import HTTPException
from src.gml.db import health_check

@app.get("/health/database")
async def check_db():
    if await health_check():
        return {"status": "healthy"}
    raise HTTPException(status_code=503, detail="Database unhealthy")
```

## Standalone Usage

### DatabaseSession Context Manager

For non-FastAPI code (scripts, background tasks, tests).

```python
from src.gml.db import DatabaseSession

async def background_task():
    async with DatabaseSession() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        # Automatic commit and cleanup
```

**Features:**
- Automatic commit on success
- Automatic rollback on exception
- Automatic session cleanup
- Clean async context manager pattern

### Manual Session Management

```python
from src.gml.db import AsyncSessionLocal

async def manual_session():
    session = AsyncSessionLocal()
    try:
        # Database operations
        result = await session.execute(select(User))
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

## Common Operations

### Create (Insert)

```python
async with DatabaseSession() as db:
    user = User(email="user@example.com", name="John")
    db.add(user)
    # Commit happens automatically
```

### Read (Select)

```python
from sqlalchemy import select

async with DatabaseSession() as db:
    # Select all
    result = await db.execute(select(User))
    users = result.scalars().all()

    # Select one
    result = await db.execute(
        select(User).where(User.id == 1)
    )
    user = result.scalar_one_or_none()

    # Select with filter
    result = await db.execute(
        select(User).where(User.email.like("%@example.com"))
    )
    users = result.scalars().all()
```

### Update

```python
async with DatabaseSession() as db:
    result = await db.execute(
        select(User).where(User.id == 1)
    )
    user = result.scalar_one()

    user.name = "Updated Name"
    # Commit happens automatically
```

### Delete

```python
async with DatabaseSession() as db:
    result = await db.execute(
        select(User).where(User.id == 1)
    )
    user = result.scalar_one()

    await db.delete(user)
    # Commit happens automatically
```

### Bulk Insert

```python
async with DatabaseSession() as db:
    users = [
        User(email=f"user{i}@example.com", name=f"User {i}")
        for i in range(100)
    ]
    db.add_all(users)
```

## Advanced Queries

### Pagination

```python
async def get_users_paginated(page: int = 1, per_page: int = 20):
    async with DatabaseSession() as db:
        offset = (page - 1) * per_page
        result = await db.execute(
            select(User)
            .offset(offset)
            .limit(per_page)
        )
        return result.scalars().all()
```

### Ordering

```python
from sqlalchemy import desc

async with DatabaseSession() as db:
    # Ascending
    result = await db.execute(
        select(User).order_by(User.name)
    )

    # Descending
    result = await db.execute(
        select(User).order_by(desc(User.created_at))
    )
```

### Aggregation

```python
from sqlalchemy import func

async with DatabaseSession() as db:
    # Count
    result = await db.execute(
        select(func.count(User.id))
    )
    count = result.scalar()

    # Group by
    result = await db.execute(
        select(User.status, func.count(User.id))
        .group_by(User.status)
    )
    stats = result.all()
```

### Joins

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async with DatabaseSession() as db:
    # Eager loading with selectinload
    result = await db.execute(
        select(User).options(selectinload(User.posts))
    )
    users = result.scalars().all()

    # Join
    result = await db.execute(
        select(User, Post)
        .join(Post, User.id == Post.user_id)
    )
    results = result.all()
```

## Utility Functions

### execute_raw_query()

Execute raw SQL (use sparingly).

```python
from src.gml.db import execute_raw_query

results = await execute_raw_query(
    "SELECT * FROM users WHERE created_at > NOW() - INTERVAL '7 days'"
)
```

### get_database_info()

Get database metadata.

```python
from src.gml.db import get_database_info

info = await get_database_info()
print(f"Database: {info['database']}")
print(f"User: {info['user']}")
print(f"Version: {info['version']}")
```

### health_check()

Verify database connectivity.

```python
from src.gml.db import health_check

if await health_check():
    print("Database is healthy")
else:
    print("Database is down")
```

## Error Handling

### Automatic Rollback

```python
from sqlalchemy.exc import SQLAlchemyError

try:
    async with DatabaseSession() as db:
        user = User(email="duplicate@example.com", name="Test")
        db.add(user)
        # If exception occurs, automatic rollback
except SQLAlchemyError as e:
    print(f"Database error: {e}")
```

### Manual Error Handling

```python
from sqlalchemy.exc import IntegrityError

try:
    async with DatabaseSession() as db:
        user = User(email="test@example.com", name="Test")
        db.add(user)
except IntegrityError:
    print("User already exists")
```

## Testing

### Test with Mock Database

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from src.gml.db import Base

@pytest.fixture
async def test_db():
    # Create test database engine
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_db",
        echo=True
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
```

### Test with In-Memory SQLite

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from src.gml.db import Base

@pytest.fixture
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()
```

## Performance Optimization

### Connection Pool Tuning

Adjust in `.env` for production:

```bash
# Connection pool settings (via database_pool_size property)
ENVIRONMENT=production  # Sets pool_size=20
```

### Query Optimization

```python
# Use select() instead of ORM query()
from sqlalchemy import select

# ✓ Efficient
result = await db.execute(select(User).where(User.id == 1))

# ✗ Avoid (legacy)
# user = await db.query(User).filter(User.id == 1).first()
```

### Batch Operations

```python
# Bulk insert
users = [User(email=f"user{i}@example.com") for i in range(1000)]
async with DatabaseSession() as db:
    db.add_all(users)
```

### Index Usage

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)  # Indexed
    name = Column(String)  # Not indexed
```

## Best Practices

1. **Always use dependency injection in FastAPI**
   ```python
   # ✓ Good
   async def handler(db: AsyncSession = Depends(get_db)):
       pass

   # ✗ Bad
   async def handler():
       db = AsyncSessionLocal()  # Manual management
   ```

2. **Use DatabaseSession for non-FastAPI code**
   ```python
   # ✓ Good
   async with DatabaseSession() as db:
       pass

   # ✗ Bad - no cleanup
   db = AsyncSessionLocal()
   ```

3. **Prefer ORM over raw SQL**
   ```python
   # ✓ Good
   result = await db.execute(select(User))

   # ✗ Avoid
   result = await execute_raw_query("SELECT * FROM users")
   ```

4. **Use type hints**
   ```python
   from sqlalchemy.ext.asyncio import AsyncSession

   async def get_user(db: AsyncSession, user_id: int) -> User | None:
       result = await db.execute(select(User).where(User.id == user_id))
       return result.scalar_one_or_none()
   ```

5. **Handle exceptions appropriately**
   ```python
   from sqlalchemy.exc import IntegrityError, NoResultFound

   try:
       user = result.scalar_one()
   except NoResultFound:
       raise HTTPException(status_code=404)
   except IntegrityError:
       raise HTTPException(status_code=409)
   ```

## Troubleshooting

### Connection Issues

```python
# Test connectivity
if not await health_check():
    print("Database connection failed")
    info = await get_database_info()
    print(info)
```

### Pool Exhaustion

If you see "QueuePool limit exceeded":

1. Check for uncommitted sessions
2. Ensure proper session cleanup
3. Increase pool_size in settings
4. Review long-running queries

### Debug Logging

Enable in `.env`:

```bash
DEBUG=true  # Enables SQL query logging
LOG_LEVEL=DEBUG
```

### Migration Issues

```python
# Recreate all tables (development only)
from src.gml.db import Base, engine

async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)
    await conn.run_sync(Base.metadata.create_all)
```

## Configuration

All settings are loaded from `.env` via the config module:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/gml_db
DEBUG=false
ENVIRONMENT=production
```

**Automatic Settings:**
- `pool_size`: 5 (dev) or 20 (prod) based on `ENVIRONMENT`
- `echo`: Matches `DEBUG` setting
- Connection pooling enabled automatically
- Health checks enabled automatically

## Examples

See `examples/database_usage.py` for complete working examples including:
- Basic CRUD operations
- Transaction handling
- Query patterns
- FastAPI integration
- Health checks
- Cleanup procedures

Run examples:

```bash
python examples/database_usage.py
```

## API Reference

### Functions

- `get_db() -> AsyncGenerator[AsyncSession, None]` - FastAPI dependency
- `init_db() -> None` - Initialize database tables
- `close_db() -> None` - Close all connections
- `health_check() -> bool` - Check database health
- `execute_raw_query(query: str) -> list` - Execute raw SQL
- `get_database_info() -> dict` - Get database metadata

### Classes

- `DatabaseSession` - Context manager for sessions
- `Base` - Declarative base for models

### Objects

- `engine: AsyncEngine` - Database engine instance
- `AsyncSessionLocal` - Session factory

## See Also

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Async PostgreSQL with asyncpg](https://magicstack.github.io/asyncpg/)
