"""
Database models — the schema for everything Jarvis remembers.

Why these tables:
    Directly maps to what the original project spec calls out: user
    preferences, devices, rooms, automation rules, notes, and
    conversation history/summaries. Each is a separate table rather
    than one big generic "memory blob" table, so queries stay simple
    and each concept can evolve its own shape independently (e.g.
    devices will likely grow fields like `last_seen` in Module 5 that
    have no meaning for a note).

Design choice:
    SQLAlchemy's declarative ORM. Each class below is both the Python
    object repositories work with AND the table definition — one
    source of truth for the schema, no separate SQL migration files to
    keep in sync by hand while the schema is still evolving this
    quickly (see database.py for the tradeoffs of that choice).
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # A short human-readable label, e.g. auto-generated from the first
    # message. Nullable — not every conversation needs one immediately.
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    messages: Mapped[list["StoredMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="StoredMessage.created_at"
    )


class StoredMessage(Base):
    """
    Named StoredMessage (not Message) to avoid colliding with
    backend.ai.base.Message, the lightweight dataclass the AI engine
    works with in memory. Repositories translate between the two.
    """

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Preference(Base):
    """
    Simple key-value store for user preferences, e.g. key="favorite_music_genre",
    value="jazz". Deliberately generic (not a fixed schema of known
    preference types) since the range of things Jarvis might need to
    remember about you is open-ended and will grow with new
    integrations — a fixed column-per-preference schema would need a
    migration every time.
    """

    __tablename__ = "preferences"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    devices: Mapped[list["Device"]] = relationship(back_populates="room")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100))
    # Free-form for now (e.g. "light", "plug", "thermostat") — becomes
    # more structured once Module 5 integrates real smart-home services
    # and we know what device types actually need distinct handling.
    device_type: Mapped[str] = mapped_column(String(50))
    room_id: Mapped[str | None] = mapped_column(ForeignKey("rooms.id"), nullable=True)

    room: Mapped["Room | None"] = relationship(back_populates="devices")


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # Free-form description of what the automation does for now (e.g.
    # "turn off all lights and lock the door"). Module 5+ will likely
    # add a structured trigger/action schema once there's a real
    # automation engine to execute these — this table exists now so
    # the AI can already remember automations even before that engine
    # is built.
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
