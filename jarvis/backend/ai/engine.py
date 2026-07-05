"""
AI Engine — the public entry point for AI reasoning in Jarvis.

Why this exists:
    Every other module (voice, gateway, memory) should only ever talk
    to `AIEngine.respond()`. This is the one place that knows about
    routing, providers, and fallback — everything else in the app stays
    completely unaware of which provider actually handled a request.

Flow for one request:
    1. Add the user's message to the conversation.
    2. Ask the router to classify it into a category (everyday
       conversation, app control, smart home, weather, memory/
       preferences, automation -> LOCAL; code, planning, research,
       document summary -> CLOUD).
    3. Call the provider configured for that tier
       (settings.ai_local_provider / settings.ai_cloud_provider).
    4. If the request was routed LOCAL, check the response for
       uncertainty language. If it reads as unsure, escalate and
       re-answer using the cloud provider instead — this covers
       "questions the local model isn't confident about."
    5. If the chosen provider is unavailable entirely (not configured,
       or local model not running), fall back to settings.ai_fallback_provider.
    6. Return the response and record it in conversation history.

Adding a new provider later:
    1. Write a new file in backend/ai/providers/ implementing AIProvider.
    2. Add one line to the _providers dict below.
    3. Point ai_local_provider / ai_cloud_provider / ai_fallback_provider
       at it via config — no other code changes needed.
"""

from dataclasses import dataclass

from backend.ai.base import AIProvider, AIResponse, ProviderUnavailableError
from backend.ai.conversation import Conversation
from backend.ai.providers.anthropic_provider import AnthropicProvider
from backend.ai.providers.gemini_provider import GeminiProvider
from backend.ai.providers.ollama_provider import OllamaProvider
from backend.ai.providers.openai_provider import OpenAIProvider
from backend.ai.router import classify, is_local_category, response_seems_uncertain
from backend.core.config import settings
from backend.core.event_bus import Event, event_bus
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)


class AllProvidersUnavailableError(Exception):
    """Raised when neither the selected provider nor the fallback could handle the request."""


@dataclass
class EngineResult:
    """
    What `AIEngine.respond()` returns — the provider's response plus
    the routing decisions made along the way. Kept separate from
    `AIResponse` (which is what a provider adapter returns) because
    routing metadata (category, whether it escalated) is a concern of
    the engine, not of any individual provider.
    """

    text: str
    provider_name: str
    model_name: str
    category: str
    routed_local: bool
    escalated_for_confidence: bool


class AIEngine:
    def __init__(self) -> None:
        # Every known provider is instantiated once here. Providers that
        # aren't configured (missing API key, local server not running)
        # simply report is_available() == False when asked — they don't
        # need to be conditionally excluded from this registry.
        self._providers: dict[str, AIProvider] = {
            "ollama": OllamaProvider(),
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "anthropic": AnthropicProvider(),
        }

    async def respond(
        self, conversation: Conversation, user_message: str, *, is_offline: bool = False
    ) -> EngineResult:
        """
        Sends a user message through the full pipeline and returns the
        AI's response plus routing metadata. Updates the conversation
        history in place.

        `is_offline` will be wired up to a real connectivity check in a
        later module; for now it defaults to False and exists so the
        offline-forces-local behavior is already supported end to end.
        """
        conversation.add_user_message(user_message)
        latest = conversation.latest_user_message

        category = classify(latest, is_offline=is_offline)
        routed_local = is_local_category(category)
        primary_name = settings.ai_local_provider if routed_local else settings.ai_cloud_provider

        response = await self._generate_with_fallback(primary_name, conversation)
        escalated = False

        # Confidence-based escalation: a locally-routed response that
        # reads as unsure gets a second attempt from the cloud provider.
        if routed_local and response_seems_uncertain(
            response.text, settings.ai_uncertainty_phrase_list
        ):
            logger.info(
                f"Local response seemed uncertain — escalating to "
                f"'{settings.ai_cloud_provider}'"
            )
            try:
                response = await self._generate_with_fallback(
                    settings.ai_cloud_provider, conversation
                )
                escalated = True
            except AllProvidersUnavailableError:
                # Keep the original (uncertain) local response rather
                # than failing outright — offline-first still applies.
                logger.warning(
                    "Escalation to cloud failed; returning original local response"
                )

        conversation.add_assistant_message(response.text)

        await event_bus.publish(
            Event(
                name="ai_response_ready",
                payload={
                    "provider": response.provider_name,
                    "model": response.model_name,
                    "category": category.value,
                    "routed_local": routed_local,
                    "escalated_for_confidence": escalated,
                },
                source="ai.engine",
            )
        )

        return EngineResult(
            text=response.text,
            provider_name=response.provider_name,
            model_name=response.model_name,
            category=category.value,
            routed_local=routed_local,
            escalated_for_confidence=escalated,
        )

    async def _generate_with_fallback(
        self, primary_name: str, conversation: Conversation
    ) -> AIResponse:
        primary = self._providers.get(primary_name)
        if primary is None:
            logger.warning(f"Unknown provider '{primary_name}' in config — check .env")
        else:
            try:
                logger.info(f"Routing request to provider '{primary_name}'")
                return await primary.generate(conversation.messages)
            except ProviderUnavailableError as exc:
                logger.warning(f"Provider '{primary_name}' unavailable: {exc}")

        fallback_name = settings.ai_fallback_provider
        if fallback_name == primary_name:
            raise AllProvidersUnavailableError(
                f"Primary provider '{primary_name}' failed and is also the configured fallback."
            )

        fallback = self._providers.get(fallback_name)
        if fallback is None:
            raise AllProvidersUnavailableError(
                f"Fallback provider '{fallback_name}' is not a known provider."
            )

        try:
            logger.info(f"Falling back to provider '{fallback_name}'")
            return await fallback.generate(conversation.messages)
        except ProviderUnavailableError as exc:
            raise AllProvidersUnavailableError(
                f"Both '{primary_name}' and fallback '{fallback_name}' were unavailable. "
                f"Last error: {exc}"
            ) from exc


# Application-wide singleton, same pattern as event_bus.
ai_engine = AIEngine()
