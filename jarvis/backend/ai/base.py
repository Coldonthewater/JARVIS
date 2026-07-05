"""
The AIProvider interface — the contract every AI backend must follow.

Why this exists:
    This is the entire reason a "hybrid, any-provider" AI system is
    possible without rewriting the app every time we add a provider.
    `engine.py` and `router.py` only ever talk to this interface — they
    have no idea whether they're talking to a local Ollama model, GPT,
    Gemini, or something we haven't added yet. As long as a new provider
    implements this interface, it plugs in immediately.

Design choice:
    We use Python's `Protocol` (structural typing) rather than an
    abstract base class. This is a style choice: any class with a
    matching `generate()` method satisfies the interface, without
    needing to explicitly inherit from a base class. Either approach
    would work — Protocol keeps provider files a little simpler.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Message:
    """
    One message in a conversation, in Jarvis's internal format.

    Every provider adapter is responsible for translating a list of
    these into whatever shape its specific API expects (and translating
    the response back into an AIResponse).
    """

    role: str  # "user", "assistant", or "system"
    content: str


@dataclass
class AIResponse:
    """
    A normalized response from any provider, regardless of which one
    actually generated it. This is what the rest of Jarvis works with —
    it never touches a provider's raw API response directly.
    """

    text: str
    provider_name: str
    model_name: str
    # Populated when available; not all providers report token usage
    # the same way, so this is best-effort and may be None.
    input_tokens: int | None = None
    output_tokens: int | None = None


class ProviderUnavailableError(Exception):
    """
    Raised by a provider adapter when it cannot fulfill a request —
    e.g., a local model isn't running, or a cloud API key is missing
    or invalid. The engine catches this to decide whether to fall back
    to another provider.
    """


class AIProvider(Protocol):
    """
    The interface every AI provider adapter must implement.

    A provider is considered "pluggable" the moment a class implements
    both of these methods with these signatures — no registration
    step beyond adding it to the provider registry in engine.py.
    """

    name: str  # short identifier, e.g. "ollama", "openai", "gemini"

    async def generate(self, messages: list[Message]) -> AIResponse:
        """
        Send the conversation to this provider and return its reply.

        Raises:
            ProviderUnavailableError: if the provider cannot be reached
                or is not configured (e.g. missing API key).
        """
        ...

    async def is_available(self) -> bool:
        """
        Cheap check for whether this provider can currently be used
        (e.g., API key is set, or local server responds to a ping).
        Used by the router/engine to decide on fallback before even
        attempting a full request.
        """
        ...
