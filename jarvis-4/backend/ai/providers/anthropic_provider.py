"""
Anthropic provider — Claude, available as one of the cloud options.

Setup:
    Requires an API key from https://console.anthropic.com
    (a developer key, billed by usage — separate from a claude.ai login).
    Set ANTHROPIC_API_KEY in config/.env.
"""

from anthropic import AsyncAnthropic, APIConnectionError, AuthenticationError, AnthropicError

from backend.ai.base import AIResponse, Message, ProviderUnavailableError
from backend.core.config import settings
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self) -> None:
        self.model = DEFAULT_MODEL
        self._client: AsyncAnthropic | None = None
        if settings.anthropic_api_key:
            self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def is_available(self) -> bool:
        return self._client is not None

    async def generate(self, messages: list[Message]) -> AIResponse:
        if self._client is None:
            raise ProviderUnavailableError(
                "ANTHROPIC_API_KEY is not set in config/.env"
            )

        # Anthropic takes the system prompt as a separate top-level
        # argument rather than a message with role "system".
        system_prompt = "\n".join(m.content for m in messages if m.role == "system")
        conversation = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt or "You are Jarvis, a helpful personal assistant.",
                messages=conversation,
            )
        except AuthenticationError as exc:
            raise ProviderUnavailableError(
                "Anthropic rejected the API key — check ANTHROPIC_API_KEY in config/.env"
            ) from exc
        except APIConnectionError as exc:
            raise ProviderUnavailableError(
                "Could not connect to Anthropic — check your internet connection"
            ) from exc
        except AnthropicError as exc:
            raise ProviderUnavailableError(f"Anthropic API error: {exc}") from exc

        text = "".join(block.text for block in response.content if block.type == "text")

        return AIResponse(
            text=text,
            provider_name=self.name,
            model_name=self.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
