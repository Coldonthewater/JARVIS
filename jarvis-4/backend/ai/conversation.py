"""
Conversation — holds the message history for a single conversation
session, independent of which provider ends up handling any given turn.

Why this exists:
    Since the router can send different messages in the same
    conversation to different providers (one to the local model, the
    next to GPT), the message history itself needs to live outside any
    one provider. This class is that shared history.

    As of Module 4 (Memory), conversations are persisted to the
    database by backend/memory — this class itself stays storage-agnostic
    (it's just an in-memory list for the duration of one request/session),
    and `from_history()` lets the memory layer rehydrate one from stored
    rows without duplicating the system prompt.
"""

from backend.ai.base import Message

DEFAULT_SYSTEM_PROMPT = (
    "You are Jarvis, a helpful, concise personal AI assistant. "
    "Keep responses clear and to the point unless the user asks for detail."
)


class Conversation:
    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> None:
        self._messages: list[Message] = [Message(role="system", content=system_prompt)]

    @classmethod
    def from_history(
        cls, history: list[Message], system_prompt: str = DEFAULT_SYSTEM_PROMPT
    ) -> "Conversation":
        """
        Rebuilds a Conversation from previously stored messages (e.g.
        loaded from the database), without adding a duplicate system
        prompt if the history didn't include one.
        """
        conversation = cls(system_prompt=system_prompt)
        if history and history[0].role == "system":
            conversation._messages = list(history)
        else:
            conversation._messages.extend(history)
        return conversation

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
