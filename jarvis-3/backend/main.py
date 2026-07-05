"""
Jarvis backend entry point.

Module 1 proved the foundation (config, logging, event bus) boots
cleanly. Module 2 adds a real terminal chat loop against the AI engine,
so you can talk to Jarvis and see the hybrid local/cloud routing work.

In later modules, this will grow into the place where we:
  - start the FastAPI gateway server (replacing this terminal loop)
  - connect the memory store
  - load enabled integrations
  - start the voice pipeline

Run it with:
    python -m backend.main
"""

import asyncio

from backend.ai.conversation import Conversation
from backend.ai.engine import AllProvidersUnavailableError, ai_engine
from backend.core.config import settings
from backend.core.event_bus import Event, event_bus
from backend.core.logging_setup import get_logger

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
    Simple terminal chat loop to manually test the AI engine end to end.
    This will be replaced by the gateway (Module 3) and voice (Module 6)
    as real ways to talk to Jarvis — this is just for development.
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
            response = await ai_engine.respond(conversation, user_input)
            print(f"Jarvis ({response.provider_name}/{response.model_name}): {response.text}\n")
        except AllProvidersUnavailableError as exc:
            logger.error(f"No provider could handle that request: {exc}")
            print(
                "Jarvis: I couldn't reach any AI provider. Check that Ollama is "
                "running, or that an API key is set in config/.env.\n"
            )


async def main() -> None:
    logger.info(f"Starting {settings.app_name} ({settings.environment} environment)")
    logger.info(f"Gateway will run on {settings.gateway_host}:{settings.gateway_port}")

    event_bus.subscribe("system_startup", _on_system_startup)
    event_bus.subscribe("ai_response_ready", _on_ai_response_ready)
    await event_bus.publish(
        Event(
            name="system_startup",
            payload={"message": "Core foundation initialized"},
            source="main",
        )
    )

    logger.info("Foundation + AI engine ready.")
    await _run_chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
