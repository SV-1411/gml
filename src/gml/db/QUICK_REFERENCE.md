# Database Module - Quick Reference

## Import

```python
from src.gml.db import (
    Base,              # Declarative base for models
    engine,            # Database engine
    AsyncSessionLocal, # Session factory
    get_db,            # FastAPI dependency
    init_db,           # Initialize tables
    close_db,          # Close connections
    health_check,      # Check database health
    DatabaseSession,   # Context manager
)
```

## Define Model

```python
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
```

## FastAPI Usage

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

@app.post("/users")
async def create_user(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    user = User(email=email)
    db.add(user)
    await db.flush()
    return user

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

## Standalone Usage

```python
from src.gml.db import DatabaseSession

async def my_function():
    async with DatabaseSession() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
```

## CRUD Operations

### Create
```python
async with DatabaseSession() as db:
    user = User(email="test@example.com", name="Test")
    db.add(user)
```

### Read
```python
async with DatabaseSession() as db:
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one_or_none()
```

### Update
```python
async with DatabaseSession() as db:
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one()
    user.name = "Updated"
```

### Delete
```python
async with DatabaseSession() as db:
    result = await db.execute(select(User).where(User.id == 1))
    user = result.scalar_one()
    await db.delete(user)
```

## Common Queries

### Filter
```python
result = await db.execute(
    select(User).where(User.email.like("%@example.com"))
)
```

### Order
```python
from sqlalchemy import desc
result = await db.execute(
    select(User).order_by(desc(User.created_at))
)
```

### Limit/Offset
```python
result = await db.execute(
    select(User).offset(10).limit(20)
)
```

### Count
```python
from sqlalchemy import func
result = await db.execute(
    select(func.count(User.id))
)
count = result.scalar()
```

## Application Lifecycle

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

## Health Check

```python
from src.gml.db import health_check

if await health_check():
    print("Database is healthy")
```

## Error Handling

```python
from sqlalchemy.exc import IntegrityError, NoResultFound

try:
    async with DatabaseSession() as db:
        user = User(email="duplicate@example.com")
        db.add(user)
except IntegrityError:
    print("Duplicate email")
except NoResultFound:
    print("User not found")
```

## Configuration

Set in `.env`:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/gml_db
DEBUG=false
ENVIRONMENT=production
```

Automatic settings:
- Pool size: 5 (dev) / 20 (prod)
- SQL logging: Enabled when DEBUG=true
- Connection pooling: Automatic
- Health checks: Pre-ping enabled

## Key Features

- Async/await support throughout
- Automatic transaction management
- Connection pooling with health checks
- FastAPI integration ready
- Type-safe with full type hints
- Debug logging support
- Proper error handling
- Clean resource management
