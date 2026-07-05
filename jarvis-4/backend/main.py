"""
Jarvis backend entry point.

By default, this starts the gateway (REST + WebSocket API) — the real
way any client (desktop, mobile, wall display, AR glasses) talks to
Jarvis going forward. A terminal chat loop is still available for
quick manual testing without needing a client.

First run: if config/.env doesn't exist yet, a setup wizard runs
automatically below — no manual file editing required to get started.
Re-run it anytime with `python -m backend.setup`.

Run it with:
    python -m backend.main            # starts the gateway server
    python -m backend.main --chat     # terminal chat loop instead (dev/testing only)
"""

import asyncio
import sys

# Runs the first-time setup wizard if config/.env doesn't exist yet.
# This has to happen before any import below that reads settings
# (which is nearly everything), so it's placed here rather than
# deferred into main() — Python executes module-level statements
# top-to-bottom, so this simply runs before the imports that follow it.
from backend.setup import ensure_configured

ensure_configured()

import uvicorn

from backend.ai.conversation import Conversation
from backend.ai.engine import AllProvidersUnavailableError, ai_engine
from backend.core.config import settings
from backend.core.event_bus import Event, event_bus
from backend.core.logging_setup import get_logger
from backend.gateway.rest.app import create_app

logger = get_logger(__name__)


async def _on_system_startup(event: Event) -> None:
    """Example event handler — proves the event bus delivers events end to end."""
    logger.info(f"Handled startup event from '{event.source}': {event.payload}")


async def _on_ai_response_ready(event: Event) -> None:
    escalated_note = " [escalated from local]" if event.payload.get("escalated_for_confidence") else ""
    tier = "local" if event.payload.get("routed_local") else "cloud"
    logger.info(
        f"AI responded via '{event.payload['provider']}' "
        f"(category: {event.payload['category']}, tier: {tier}){escalated_note}"
    )


async def _run_chat_loop() -> None:
    """
    Terminal chat loop for manually testing the AI engine without a
    real client — useful during development, or to sanity-check a
    provider/config change quickly.
    """
    print("\nJarvis AI Engine — type a message, or 'quit' to exit.\n")
    conversation = Conversation()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        try:
            result = await ai_engine.respond(conversation, user_input)
            print(f"Jarvis ({result.provider_name}/{result.model_name}): {result.text}\n")
        except AllProvidersUnavailableError as exc:
            logger.error(f"No provider could handle that request: {exc}")
            print(
                "Jarvis: I couldn't reach any AI provider. Check that Ollama is "
                "running, or that an API key is set in config/.env.\n"
            )


def _publish_startup_events() -> None:
    event_bus.subscribe("system_startup", _on_system_startup)
    event_bus.subscribe("ai_response_ready", _on_ai_response_ready)


async def _run_gateway() -> None:
    _publish_startup_events()
    await event_bus.publish(
        Event(
            name="system_startup",
            payload={"message": "Core foundation initialized"},
            source="main",
        )
    )

    app = create_app()
    config = uvicorn.Config(
        app, host=settings.gateway_host, port=settings.gateway_port, log_level="warning"
    )
    server = uvicorn.Server(config)
    await server.serve()


async def _run_chat_mode() -> None:
    _publish_startup_events()
    logger.info(f"Starting {settings.app_name} ({settings.environment} environment) — chat mode")
    await event_bus.publish(
        Event(
            name="system_startup",
            payload={"message": "Core foundation initialized"},
            source="main",
        )
    )
    await _run_chat_loop()


if __name__ == "__main__":
    if "--chat" in sys.argv:
        asyncio.run(_run_chat_mode())
    else:
        logger.info(f"Starting {settings.app_name} ({settings.environment} environment) — gateway mode")
        logger.info(f"Gateway listening on http://{settings.gateway_host}:{settings.gateway_port}")
        logger.info(f"API docs available at http://{settings.gateway_host}:{settings.gateway_port}/docs")
        asyncio.run(_run_gateway())
