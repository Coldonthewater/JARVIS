"""
Conversation — holds the message history for a single conversation
session, independent of which provider ends up handling any given turn.

Why this exists:
    Since the router can send different messages in the same
    conversation to different providers (one to the local model, the
    next to GPT), the message history itself needs to live outside any
    one provider. This class is that shared history.

    In Module 4 (Memory), conversations will be persisted to the
    database so history survives a restart. For now, this is in-memory
    only — good enough to prove the AI engine works end to end.
"""

from backend.ai.base import Message

DEFAULT_SYSTEM_PROMPT = (
    "You are Jarvis, a helpful, concise personal AI assistant. "
    "Keep responses clear and to the point unless the user asks for detail."
)


class Conversation:
    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> None:
        self._messages: list[Message] = [Message(role="system", content=system_prompt)]

    def add_user_message(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str) -> None:
        self._messages.append(Message(role="assistant", content=content))

    @property
    def messages(self) -> list[Message]:
        """Read-only view of the full history, sent to whichever provider handles the next turn."""
        return list(self._messages)

    @property
    def latest_user_message(self) -> Message:
        """The most recent user message — used by the router for classification."""
        for message in reversed(self._messages):
            if message.role == "user":
                return message
        raise ValueError("No user message has been added yet")
