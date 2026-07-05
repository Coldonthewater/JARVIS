"""
Conversation repository — persists conversation history to the
database, and reconstructs it for the AI engine.

Why this exists:
    This is what replaces the gateway's placeholder in-memory
    conversation dict from Module 3. Every module that needs to store
    or load a conversation goes through this repository rather than
    touching SQLAlchemy models directly — keeps the ORM details out of
    the gateway and AI layers.
"""

from sqlalchemy import select

from backend.ai.base import Message as EngineMessage
from backend.memory.database import get_session
from backend.memory.models import Conversation as ConversationRow
from backend.memory.models import StoredMessage


class ConversationRepository:
    async def create(self) -> str:
        """Creates a new, empty conversation and returns its id."""
        async with get_session() as session:
            row = ConversationRow()
            session.add(row)
            await session.commit()
            return row.id

    async def exists(self, conversation_id: str) -> bool:
        async with get_session() as session:
            result = await session.get(ConversationRow, conversation_id)
            return result is not None

    async def load_messages(self, conversation_id: str) -> list[EngineMessage]:
        """
        Loads a conversation's full message history as the lightweight
        `EngineMessage` objects the AI engine works with — repositories
        are responsible for this translation so the AI layer never
        needs to know about the database schema.
        """
        async with get_session() as session:
            result = await session.execute(
                select(StoredMessage)
                .where(StoredMessage.conversation_id == conversation_id)
                .order_by(StoredMessage.created_at)
            )
            rows = result.scalars().all()
            return [EngineMessage(role=row.role, content=row.content) for row in rows]

    async def append_message(self, conversation_id: str, role: str, content: str) -> None:
        async with get_session() as session:
            session.add(
                StoredMessage(conversation_id=conversation_id, role=role, content=content)
            )
            await session.commit()

    async def list_conversations(self) -> list[dict]:
        """Lightweight summary list — id, title, created_at — not full message history."""
        async with get_session() as session:
            result = await session.execute(select(ConversationRow).order_by(ConversationRow.created_at.desc()))
            rows = result.scalars().all()
            return [
                {"id": row.id, "title": row.title, "created_at": row.created_at.isoformat()}
                for row in rows
            ]


# Application-wide singleton, same pattern as other repositories/registries.
conversation_repository = ConversationRepository()
