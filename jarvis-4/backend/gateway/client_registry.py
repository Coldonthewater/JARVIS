"""
Client Registry — tracks which clients are connected and what they
can do, so the gateway can tailor what it sends to each one.

Why this exists:
    This is the core of "any client can connect without backend
    changes." A desktop app, a phone, a wall display, and AR glasses
    are all wildly different — different screens, different input
    methods, different bandwidth. Rather than hardcoding logic like
    "if client is mobile, do X," each client declares its own
    capabilities when it connects, and the gateway/other modules make
    decisions based on that declaration instead of a hardcoded type
    check.

    Adding a brand new client type later (say, a smartwatch) requires
    zero backend code changes — it just connects and declares what it
    supports.

Design choice:
    This is in-memory for now, which is fine — client sessions are
    inherently short-lived (they reconnect on every app launch), unlike
    conversation history or preferences, which belong in the database
    (Module 4).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from backend.core.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class ClientCapabilities:
    """
    What a connecting client says it supports. Every field defaults to
    False/None so a minimal client can connect by declaring almost
    nothing — capabilities are opt-in, not opt-out.
    """

    has_microphone: bool = False
    has_speaker: bool = False
    has_display: bool = False
    supports_push_notifications: bool = False
    # Free-form, e.g. "desktop", "mobile", "wall_display", "ar_glasses".
    # Not used for hardcoded branching — only for logging/debugging and
    # any future analytics. Behavior should be driven by the specific
    # capability flags above, not this label.
    client_type: str = "unknown"


@dataclass
class ConnectedClient:
    client_id: str
    capabilities: ClientCapabilities
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ClientRegistry:
    """
    In-memory registry of currently connected clients.

    Usage:
        registry = ClientRegistry()
        client_id = registry.register(capabilities)
        ...
        registry.unregister(client_id)
    """

    def __init__(self) -> None:
        self._clients: dict[str, ConnectedClient] = {}

    def register(self, capabilities: ClientCapabilities) -> str:
        client_id = str(uuid4())
        self._clients[client_id] = ConnectedClient(
            client_id=client_id, capabilities=capabilities
        )
        logger.info(
            f"Client registered: {client_id} (type={capabilities.client_type})"
        )
        return client_id

    def unregister(self, client_id: str) -> None:
        if client_id in self._clients:
            del self._clients[client_id]
            logger.info(f"Client disconnected: {client_id}")

    def get(self, client_id: str) -> ConnectedClient | None:
        return self._clients.get(client_id)

    def all_clients(self) -> list[ConnectedClient]:
        return list(self._clients.values())


# Application-wide singleton, same pattern as event_bus and ai_engine.
client_registry = ClientRegistry()
