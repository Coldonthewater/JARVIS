"""
Household repository — rooms, devices, automation rules, and notes.

Why grouped into one file:
    These four entities are simple, structurally similar CRUD stores
    (create/list/delete, little unique logic each) and are all
    "things Jarvis remembers about your home/routines" as opposed to
    conversation history or free-form preferences. Grouping them here
    avoids four near-identical tiny files while each is still exposed
    as its own repository class — if any of these grows real
    complexity (most likely devices, once Module 5 wires up real
    smart-home integrations), it's a clean lift into its own file at
    that point.
"""

from sqlalchemy import select

from backend.memory.database import get_session
from backend.memory.models import AutomationRule, Device, Note, Room


class RoomRepository:
    async def create(self, name: str) -> str:
        async with get_session() as session:
            row = Room(name=name)
            session.add(row)
            await session.commit()
            return row.id

    async def list_all(self) -> list[dict]:
        async with get_session() as session:
            result = await session.execute(select(Room))
            return [{"id": r.id, "name": r.name} for r in result.scalars().all()]

    async def delete(self, room_id: str) -> None:
        async with get_session() as session:
            row = await session.get(Room, room_id)
            if row:
                await session.delete(row)
                await session.commit()


class DeviceRepository:
    async def create(self, name: str, device_type: str, room_id: str | None = None) -> str:
        async with get_session() as session:
            row = Device(name=name, device_type=device_type, room_id=room_id)
            session.add(row)
            await session.commit()
            return row.id

    async def list_all(self) -> list[dict]:
        async with get_session() as session:
            result = await session.execute(select(Device))
            return [
                {"id": d.id, "name": d.name, "device_type": d.device_type, "room_id": d.room_id}
                for d in result.scalars().all()
            ]

    async def delete(self, device_id: str) -> None:
        async with get_session() as session:
            row = await session.get(Device, device_id)
            if row:
                await session.delete(row)
                await session.commit()


class AutomationRepository:
    async def create(self, name: str, description: str) -> str:
        async with get_session() as session:
            row = AutomationRule(name=name, description=description)
            session.add(row)
            await session.commit()
            return row.id

    async def list_all(self) -> list[dict]:
        async with get_session() as session:
            result = await session.execute(select(AutomationRule))
            return [{"id": a.id, "name": a.name, "description": a.description} for a in result.scalars().all()]

    async def delete(self, automation_id: str) -> None:
        async with get_session() as session:
            row = await session.get(AutomationRule, automation_id)
            if row:
                await session.delete(row)
                await session.commit()


class NoteRepository:
    async def create(self, content: str) -> str:
        async with get_session() as session:
            row = Note(content=content)
            session.add(row)
            await session.commit()
            return row.id

    async def list_all(self) -> list[dict]:
        async with get_session() as session:
            result = await session.execute(select(Note).order_by(Note.created_at.desc()))
            return [{"id": n.id, "content": n.content, "created_at": n.created_at.isoformat()} for n in result.scalars().all()]

    async def delete(self, note_id: str) -> None:
        async with get_session() as session:
            row = await session.get(Note, note_id)
            if row:
                await session.delete(row)
                await session.commit()


# Application-wide singletons.
room_repository = RoomRepository()
device_repository = DeviceRepository()
automation_repository = AutomationRepository()
note_repository = NoteRepository()
