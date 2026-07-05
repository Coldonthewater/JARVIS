"""
Conversation service — the gateway's single point of contact with
persisted conversation history.

Why this exists:
    Both the REST /chat endpoint and the WebSocket /ws/chat endpoint
    need the same three steps: load (or create) a conversation,
    hand it to the AI engine, then persist the new turn. Rather than
    duplicating that logic in both route files, it lives here once.
    This replaces the in-memory `_conversations` dict from Module 3.
"""

from backend.ai.conversation import Conversation
from backend.ai.engine import EngineResult, ai_engine
from backend.memory.repositories.conversation_repository import conversation_repository


async def get_or_create_conversation_id(conversation_id: str | None) -> str:
    if conversation_id and await conversation_repository.exists(conversation_id):
        return conversation_id
    return await conversation_repository.create()


async def send_message(conversation_id: str, user_message: str) -> EngineResult:
    """
    Loads the conversation's persisted history, sends the new message
    through the AI engine, and persists both the user message and the
    assistant's reply. Returns the engine's result for the caller
    (REST route or WebSocket handler) to relay to the client.
    """
    history = await conversation_repository.load_messages(conversation_id)
    conversation = Conversation.from_history(history)

    result = await ai_engine.respond(conversation, user_message)

    await conversation_repository.append_message(conversation_id, "user", user_message)
    await conversation_repository.append_message(conversation_id, "assistant", result.text)

    return result
