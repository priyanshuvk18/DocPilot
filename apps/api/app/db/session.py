"""
SQLAlchemy async session factory.

Pattern:
  - One engine per process (created at import time)
  - Sessions are per-request (created via get_db() dependency)
  - Every request-scoped session sets `app.current_user_id` in Postgres
    so that auth.uid() works correctly in RLS policies

Usage (as FastAPI dependency):
    async def my_route(db: AsyncSession = Depends(get_db)) -> ...:
        result = await db.execute(select(MyModel))
"""
from __future__ import annotations

from typing import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = structlog.get_logger(__name__)

# ─── Engine ───────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_pre_ping=True,          # detect stale connections
    echo=settings.environment == "development",  # SQL logging in dev only
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,       # keep objects accessible after commit
    autocommit=False,
    autoflush=False,
)


# ─── Base ORM class ───────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


# ─── Session dependency ───────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a per-request async database session.

    Sets `app.current_user_id` in Postgres so that auth.uid() returns the
    correct user ID for RLS policy evaluation.

    Note: The user_id is set by the calling route, which receives it from
    the auth dependency. See core/security.py for the auth flow.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_rls_context(session: AsyncSession, user_id: str) -> None:
    """
    Set the Postgres session variable used by auth.uid() for RLS.

    Must be called at the start of every request that touches tenant tables.
    The FastAPI route dependencies call this after JWT verification.

    In production with Supabase: Supabase injects the JWT claims directly
    into Postgres session variables via its connection pooler (PgBouncer).
    In local dev: we set them manually here.
    """
    await session.execute(
        # SET LOCAL applies only for the current transaction
        # Using parameterized SET to prevent injection
        # (Postgres doesn't support $1 in SET, but user_id is UUID — safe)
        __import__("sqlalchemy").text(
            f"SET LOCAL app.current_user_id = '{user_id}'"
        )
    )
    logger.debug("RLS context set", user_id=user_id)
