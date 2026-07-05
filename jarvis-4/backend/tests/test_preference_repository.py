"""Tests for backend/memory/repositories/preference_repository.py."""

import pytest

from backend.memory.repositories.preference_repository import PreferenceRepository


@pytest.mark.asyncio
async def test_set_and_get_round_trip(memory_db):
    repo = PreferenceRepository()
    await repo.set("favorite_color", "teal")
    assert await repo.get("favorite_color") == "teal"


@pytest.mark.asyncio
async def test_get_missing_key_returns_none(memory_db):
    repo = PreferenceRepository()
    assert await repo.get("does_not_exist") is None


@pytest.mark.asyncio
async def test_set_overwrites_existing_value(memory_db):
    repo = PreferenceRepository()
    await repo.set("favorite_color", "teal")
    await repo.set("favorite_color", "blue")
    assert await repo.get("favorite_color") == "blue"


@pytest.mark.asyncio
async def test_delete_removes_preference(memory_db):
    repo = PreferenceRepository()
    await repo.set("temp_pref", "value")
    await repo.delete("temp_pref")
    assert await repo.get("temp_pref") is None


@pytest.mark.asyncio
async def test_list_all_returns_every_preference(memory_db):
    repo = PreferenceRepository()
    await repo.set("a", "1")
    await repo.set("b", "2")
    assert await repo.list_all() == {"a": "1", "b": "2"}
