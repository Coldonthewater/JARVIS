"""
The Event Bus — the central nervous system of Jarvis.

Why this exists:
    Without an event bus, modules end up calling each other directly:
    the voice module would import the AI module, which would import the
    memory module, which would import the gateway... This creates tight
    coupling, where changing one module risks breaking three others, and
    makes it hard to add new modules later.

    Instead, modules publish events ("user_spoke", "ai_response_ready",
    "integration_status_changed") to this bus without knowing who (if
    anyone) is listening. Other modules subscribe to the events they
    care about. This means:
      - The voice module doesn't need to know the gateway exists in
        order to notify connected clients that the user said something.
      - We can add a brand new module later (e.g., a "smart home"
        module that reacts to "user_spoke" events) without touching
        any existing code.

Design choice:
    This is an in-process async pub/sub bus (not a network message
    queue like Redis/RabbitMQ). That's the right level of complexity
    for now — everything runs in one backend process. If Jarvis ever
    needs to scale across multiple processes/machines, this same
    interface (`publish`, `subscribe`) could be backed by a real message
    broker without changing the code that *uses* the bus.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from backend.core.logging_setup import get_logger

logger = get_logger(__name__)

# A handler is any async function that takes an Event and returns nothing.
EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass
class Event:
    """
    A single event flowing through the system.

    Attributes:
        name: The event type, e.g. "user_spoke", "ai_response_ready".
              Convention: lowercase, snake_case, past tense for things
              that happened (e.g. "command_executed").
        payload: Arbitrary data relevant to the event. Each event name
                 should have a documented, consistent payload shape
                 (we'll track these in docs/architecture.md as we add
                 events).
        source: Which module emitted this event, useful for debugging.
        timestamp: When the event was created (UTC).
    """

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    """
    A simple async publish/subscribe event bus.

    Usage:
        bus = EventBus()

        async def on_user_spoke(event: Event):
            print(event.payload["text"])

        bus.subscribe("user_spoke", on_user_spoke)
        await bus.publish(Event(name="user_spoke", payload={"text": "hi"}, source="voice"))
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register `handler` to be called whenever `event_name` is published."""
        self._subscribers[event_name].append(handler)
        logger.debug(f"Subscribed {handler.__qualname__} to event '{event_name}'")

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        if handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)
            logger.debug(f"Unsubscribed {handler.__qualname__} from event '{event_name}'")

    async def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers of its name.

        Handlers run concurrently (via asyncio.gather), and an error in
        one handler is logged but does NOT prevent other handlers from
        running. This matters: if a buggy "smart home" handler raises an
        exception, it should never be able to crash the "save to memory"
        handler for the same event.
        """
        handlers = self._subscribers.get(event.name, [])
        logger.debug(
            f"Publishing event '{event.name}' from '{event.source}' "
            f"to {len(handlers)} subscriber(s)"
        )

        if not handlers:
            return

        results = await asyncio.gather(
            *(self._run_handler_safely(handler, event) for handler in handlers),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error handling event '{event.name}': {result}", exc_info=result)

    @staticmethod
    async def _run_handler_safely(handler: EventHandler, event: Event) -> None:
        await handler(event)


# Application-wide singleton. Modules import this directly:
#   from backend.core.event_bus import event_bus
event_bus = EventBus()
