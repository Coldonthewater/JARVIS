"""
Jarvis backend entry point.

For now (Module 1), this file exists purely to prove that the
foundation pieces — config, logging, and the event bus — are wired
together correctly and the application boots cleanly.

In later modules, this will grow into the place where we:
  - start the FastAPI gateway server
  - initialize the AI engine
  - connect the memory store
  - load enabled integrations
  - start the voice pipeline

Run it with:
    python -m backend.main
"""

import asyncio

from backend.core.config import settings
from backend.core.event_bus import Event, event_bus
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)


async def _on_system_startup(event: Event) -> None:
    """Example event handler — proves the event bus delivers events end to end."""
    logger.info(f"Handled startup event from '{event.source}': {event.payload}")


async def main() -> None:
    logger.info(f"Starting {settings.app_name} ({settings.environment} environment)")
    logger.info(f"Gateway will run on {settings.gateway_host}:{settings.gateway_port}")

    # Demonstrate the event bus working: subscribe, then publish.
    event_bus.subscribe("system_startup", _on_system_startup)
    await event_bus.publish(
        Event(
            name="system_startup",
            payload={"message": "Core foundation initialized"},
            source="main",
        )
    )

    logger.info("Module 1 foundation is healthy. Nothing else is running yet.")


if __name__ == "__main__":
    asyncio.run(main())
