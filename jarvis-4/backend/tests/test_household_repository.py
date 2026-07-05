"""Tests for backend/memory/repositories/household_repository.py."""

import pytest

from backend.memory.repositories.household_repository import (
    AutomationRepository,
    DeviceRepository,
    NoteRepository,
    RoomRepository,
)


@pytest.mark.asyncio
async def test_room_create_and_list(memory_db):
    repo = RoomRepository()
    room_id = await repo.create("Living Room")
    rooms = await repo.list_all()
    assert any(r["id"] == room_id and r["name"] == "Living Room" for r in rooms)


@pytest.mark.asyncio
async def test_room_delete(memory_db):
    repo = RoomRepository()
    room_id = await repo.create("Kitchen")
    await repo.delete(room_id)
    rooms = await repo.list_all()
    assert not any(r["id"] == room_id for r in rooms)


@pytest.mark.asyncio
async def test_device_create_with_room(memory_db):
    room_repo = RoomRepository()
    device_repo = DeviceRepository()

    room_id = await room_repo.create("Bedroom")
    device_id = await device_repo.create("Bedside Lamp", "light", room_id=room_id)

    devices = await device_repo.list_all()
    match = next(d for d in devices if d["id"] == device_id)
    assert match["name"] == "Bedside Lamp"
    assert match["device_type"] == "light"
    assert match["room_id"] == room_id


@pytest.mark.asyncio
async def test_device_create_without_room(memory_db):
    device_repo = DeviceRepository()
    device_id = await device_repo.create("Smart Plug", "plug")
    devices = await device_repo.list_all()
    match = next(d for d in devices if d["id"] == device_id)
    assert match["room_id"] is None


@pytest.mark.asyncio
async def test_automation_create_and_list(memory_db):
    repo = AutomationRepository()
    automation_id = await repo.create("Good Morning", "Turn on lights and read the weather")
    automations = await repo.list_all()
    assert any(a["id"] == automation_id for a in automations)


@pytest.mark.asyncio
async def test_note_create_and_list(memory_db):
    repo = NoteRepository()
    note_id = await repo.create("Remember to water the plants")
    notes = await repo.list_all()
    assert any(n["id"] == note_id and n["content"] == "Remember to water the plants" for n in notes)
