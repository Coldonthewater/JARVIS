"""
Tests for backend/gateway/conversation_service.py.

The AI engine call is monkeypatched (same pattern as test_engine.py)
so these tests don't require a real provider — they verify the
persistence wiring, not AI behavior.
"""

from dataclasses import dataclass

import pytest

from backend.gateway import conversation_service


@dataclass
class FakeEngineResult:
    text: str = "hi there"
    provider_name: str = "fake"
    model_name: str = "fake-model"
    category: str = "everyday_conversation"
    routed_local: bool = True
    escalated_for_confidence: bool = False


@pytest.mark.asyncio
async def test_get_or_create_returns_new_id_when_none_given(memory_db):
    conversation_id = await conversation_service.get_or_create_conversation_id(None)
    assert conversation_id


@pytest.mark.asyncio
async def test_get_or_create_reuses_existing_id(memory_db):
    first_id = await conversation_service.get_or_create_conversation_id(None)
    second_id = await conversation_service.get_or_create_conversation_id(first_id)
    assert first_id == second_id


@pytest.mark.asyncio
async def test_get_or_create_falls_back_to_new_id_for_unknown_id(memory_db):
    conversation_id = await conversation_service.get_or_create_conversation_id("bogus-id")
    assert conversation_id != "bogus-id"


@pytest.mark.asyncio
async def test_send_message_persists_both_turns(memory_db, monkeypatch):
    async def fake_respond(conversation, message, **kwargs):
        return FakeEngineResult()

    monkeypatch.setattr("backend.gateway.conversation_service.ai_engine.respond", fake_respond)

    conversation_id = await conversation_service.get_or_create_conversation_id(None)
    result = await conversation_service.send_message(conversation_id, "hello")

    assert result.text == "hi there"

    from backend.memory.repositories.conversation_repository import conversation_repository

    history = await conversation_repository.load_messages(conversation_id)
    assert [(m.role, m.content) for m in history] == [
        ("user", "hello"),
        ("assistant", "hi there"),
    ]


@pytest.mark.asyncio
async def test_send_message_uses_prior_history(memory_db, monkeypatch):
    seen_message_counts = []

    async def fake_respond(conversation, message, **kwargs):
        seen_message_counts.append(len(conversation.messages))
        return FakeEngineResult()

    monkeypatch.setattr("backend.gateway.conversation_service.ai_engine.respond", fake_respond)

    conversation_id = await conversation_service.get_or_create_conversation_id(None)
    await conversation_service.send_message(conversation_id, "first message")
    await conversation_service.send_message(conversation_id, "second message")

    # Second call should see more history than the first (system prompt +
    # first turn's user/assistant messages already loaded).
    assert seen_message_counts[1] > seen_message_counts[0]
