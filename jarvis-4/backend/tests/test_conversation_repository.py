"""Tests for backend/memory/repositories/conversation_repository.py."""

import pytest

from backend.memory.repositories.conversation_repository import ConversationRepository


@pytest.mark.asyncio
async def test_create_returns_new_conversation_id(memory_db):
    repo = ConversationRepository()
    conversation_id = await repo.create()
    assert conversation_id
    assert await repo.exists(conversation_id) is True


@pytest.mark.asyncio
async def test_exists_returns_false_for_unknown_id(memory_db):
    repo = ConversationRepository()
    assert await repo.exists("not-a-real-id") is False


@pytest.mark.asyncio
async def test_append_and_load_messages_round_trip(memory_db):
    repo = ConversationRepository()
    conversation_id = await repo.create()

    await repo.append_message(conversation_id, "user", "hello")
    await repo.append_message(conversation_id, "assistant", "hi there")

    messages = await repo.load_messages(conversation_id)
    assert [(m.role, m.content) for m in messages] == [
        ("user", "hello"),
        ("assistant", "hi there"),
    ]


@pytest.mark.asyncio
async def test_load_messages_returns_empty_list_for_new_conversation(memory_db):
    repo = ConversationRepository()
    conversation_id = await repo.create()
    assert await repo.load_messages(conversation_id) == []


@pytest.mark.asyncio
async def test_list_conversations_includes_created_conversation(memory_db):
    repo = ConversationRepository()
    conversation_id = await repo.create()

    conversations = await repo.list_conversations()
    ids = [c["id"] for c in conversations]
    assert conversation_id in ids
