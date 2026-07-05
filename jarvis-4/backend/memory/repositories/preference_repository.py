"""
Preference repository — get/set the simple key-value preferences
Jarvis remembers about you.

Why this exists:
    Backs the AI router's `memory_preference` category and, later, any
    integration or dashboard that wants to read/write a preference
    (e.g. "favorite_music_genre", "preferred_temperature_unit").
    Kept intentionally simple (get/set/list/delete) — the interesting
    logic of *deciding* when a conversation implies a preference worth
    saving belongs elsewhere (a future module, once there's a clearer
    picture of how that extraction should work — tracked in
    docs/future-features.md), not in this storage layer.
"""

from sqlalchemy import select

from backend.memory.database import get_session
from backend.memory.models import Preference


class PreferenceRepository:
    async def set(self, key: str, value: str) -> None:
        async with get_session() as session:
            existing = await session.get(Preference, key)
            if existing:
                existing.value = value
            else:
                session.add(Preference(key=key, value=value))
            await session.commit()

    async def get(self, key: str) -> str | None:
        async with get_session() as session:
            row = await session.get(Preference, key)
            return row.value if row else None

    async def delete(self, key: str) -> None:
        async with get_session() as session:
            row = await session.get(Preference, key)
            if row:
                await session.delete(row)
                await session.commit()

    async def list_all(self) -> dict[str, str]:
        async with get_session() as session:
            result = await session.execute(select(Preference))
            return {row.key: row.value for row in result.scalars().all()}


# Application-wide singleton.
preference_repository = PreferenceRepository()
