"""
Database engine and session management.

Why this exists:
    Every repository (conversation, preference, household) needs a
    database session to talk to SQLite. This module is the single
    place that creates the engine and hands out sessions, so nothing
    else in the codebase constructs its own connection.

Design choice:
    SQLite via SQLAlchemy's async engine (with the aiosqlite driver).
    SQLite is the right starting point for a single-machine personal
    assistant — zero setup, one file, no separate server process to
    run. `settings.database_url` already points at a file under
    data/jarvis.db (see backend/core/config.py). If Jarvis ever needs
    a real client-server database (e.g. multiple always-on services
    hitting it concurrently), the swap to PostgreSQL only touches this
    file and the connection string — every repository built on top of
    SQLAlchemy's ORM stays the same.

    Schema creation uses `Base.metadata.create_all()` rather than a
    migration tool (e.g. Alembic) — appropriate for a single-developer,
    early-stage project where the schema is still evolving quickly.
    Revisit with Alembic once the schema stabilizes (tracked in
    docs/future-features.md) so schema changes don't risk data loss.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.core.logging_setup import get_logger
from backend.memory.models import Base

logger = get_logger(__name__)


def _to_async_url(url: str) -> str:
    """
    Converts a plain `sqlite:///...` URL (as stored in settings, kept
    driver-agnostic for readability) into the aiosqlite-flavored URL
    SQLAlchemy's async engine actually needs.
    """
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


_engine = create_async_engine(_to_async_url(settings.database_url), echo=False)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def init_db() -> None:
    """
    Creates all tables if they don't already exist. Safe to call every
    startup — existing tables are left untouched.
    """
    # Ensure the data/ directory exists before SQLite tries to create
    # the file inside it (SQLite won't create missing parent folders).
    from pathlib import Path

    db_path = settings.database_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"Database ready at {settings.database_url}")


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Usage:
        async with get_session() as session:
            ...

    Every repository method opens its own short-lived session via this
    context manager rather than sharing one long-lived session across
    requests — the standard, safe pattern for a request-scoped ORM
    session.
    """
    async with _session_factory() as session:
        yield session
