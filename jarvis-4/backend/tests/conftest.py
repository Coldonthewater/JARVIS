"""
Shared pytest fixtures.

`memory_db` gives tests an isolated, in-memory SQLite database instead
of touching the real data/jarvis.db file — each test starts with a
clean schema and nothing persists between tests or affects your real
Jarvis data.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import backend.memory.database as database_module
from backend.memory.models import Base


@pytest_asyncio.fixture
async def memory_db(monkeypatch):
    """
    Points backend.memory.database at a fresh in-memory SQLite engine
    for the duration of one test. StaticPool keeps the same in-memory
    database visible across the multiple short-lived sessions each
    repository call opens (without it, each new connection would see
    a blank, unrelated in-memory database).
    """
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(database_module, "_engine", test_engine)
    monkeypatch.setattr(database_module, "_session_factory", test_session_factory)

    yield

    await test_engine.dispose()
