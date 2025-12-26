"""
Example: Database Module Usage

This script demonstrates how to use the async database module
for SQLAlchemy operations in GML Infrastructure.
"""

import asyncio

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gml.db import Base, DatabaseSession, get_db, health_check, init_db


# ============================================================================
# EXAMPLE MODEL
# ============================================================================


class User(Base):
    """Example User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"


# ============================================================================
# FASTAPI INTEGRATION EXAMPLES
# ============================================================================

app = FastAPI(title="Database Example API")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("Initializing database...")
    await init_db()
    print("✓ Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    from src.gml.db import close_db

    print("Closing database connections...")
    await close_db()
    print("✓ Database closed")


@app.get("/health/db")
async def check_database_health():
    """Check database health."""
    is_healthy = await health_check()
    if is_healthy:
        return {"status": "healthy", "database": "connected"}
    raise HTTPException(status_code=503, detail="Database unhealthy")


@app.post("/users")
async def create_user(
    email: str,
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user using FastAPI dependency injection."""
    # Create new user
    new_user = User(email=email, name=name)
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    return {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
    }


@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
    }


@app.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
        for user in users
    ]


# ============================================================================
# STANDALONE USAGE EXAMPLES
# ============================================================================


async def example_basic_operations():
    """Example: Basic CRUD operations."""
    print("=" * 60)
    print("BASIC DATABASE OPERATIONS")
    print("=" * 60)

    # Initialize database (creates tables)
    print("\n1. Initializing database...")
    await init_db()

    # Create users
    print("\n2. Creating users...")
    async with DatabaseSession() as db:
        user1 = User(email="alice@example.com", name="Alice")
        user2 = User(email="bob@example.com", name="Bob")

        db.add(user1)
        db.add(user2)
        # Commit happens automatically on context exit

    print("   ✓ Users created")

    # Read users
    print("\n3. Reading users...")
    async with DatabaseSession() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            print(f"   - {user.name} ({user.email})")

    # Update user
    print("\n4. Updating user...")
    async with DatabaseSession() as db:
        result = await db.execute(select(User).where(User.email == "alice@example.com"))
        user = result.scalar_one_or_none()

        if user:
            user.name = "Alice Updated"
            print(f"   ✓ Updated: {user}")

    # Delete user
    print("\n5. Deleting user...")
    async with DatabaseSession() as db:
        result = await db.execute(select(User).where(User.email == "bob@example.com"))
        user = result.scalar_one_or_none()

        if user:
            await db.delete(user)
            print(f"   ✓ Deleted: {user.email}")


async def example_transaction_handling():
    """Example: Transaction handling with rollback."""
    print("\n" + "=" * 60)
    print("TRANSACTION HANDLING")
    print("=" * 60)

    print("\n1. Transaction with automatic commit:")
    try:
        async with DatabaseSession() as db:
            user = User(email="charlie@example.com", name="Charlie")
            db.add(user)
            # Commit happens automatically on successful exit
        print("   ✓ User created and committed")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n2. Transaction with rollback on error:")
    try:
        async with DatabaseSession() as db:
            user = User(email="charlie@example.com", name="Charlie Duplicate")
            db.add(user)
            # This will fail due to unique constraint
    except Exception as e:
        print(f"   ✓ Error caught and rolled back: {type(e).__name__}")


async def example_queries():
    """Example: Different query patterns."""
    print("\n" + "=" * 60)
    print("QUERY PATTERNS")
    print("=" * 60)

    async with DatabaseSession() as db:
        # Simple select
        print("\n1. Select all users:")
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"   Found {len(users)} users")

        # Filter query
        print("\n2. Filter by email:")
        result = await db.execute(select(User).where(User.email.like("%alice%")))
        users = result.scalars().all()
        for user in users:
            print(f"   - {user.email}")

        # Count query
        print("\n3. Count users:")
        from sqlalchemy import func

        result = await db.execute(select(func.count(User.id)))
        count = result.scalar()
        print(f"   Total users: {count}")

        # Order and limit
        print("\n4. Order by name, limit 5:")
        result = await db.execute(select(User).order_by(User.name).limit(5))
        users = result.scalars().all()
        for user in users:
            print(f"   - {user.name}")


async def example_health_check():
    """Example: Database health check."""
    print("\n" + "=" * 60)
    print("HEALTH CHECK")
    print("=" * 60)

    is_healthy = await health_check()
    print(f"\nDatabase Status: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")

    # Get detailed info
    from src.gml.db import get_database_info

    info = await get_database_info()
    print("\nDatabase Information:")
    for key, value in info.items():
        if key == "version":
            print(f"  {key}: {value[:50]}...")
        else:
            print(f"  {key}: {value}")


async def example_cleanup():
    """Example: Cleanup database connections."""
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    from src.gml.db import close_db

    print("\nClosing database connections...")
    await close_db()
    print("✓ Connections closed")


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Run all examples."""
    try:
        print("\n" + "=" * 60)
        print("DATABASE MODULE - USAGE EXAMPLES")
        print("=" * 60)

        await example_health_check()
        await example_basic_operations()
        await example_transaction_handling()
        await example_queries()
        await example_cleanup()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Run standalone examples
    asyncio.run(main())

    # To run the FastAPI app:
    # uvicorn examples.database_usage:app --reload
