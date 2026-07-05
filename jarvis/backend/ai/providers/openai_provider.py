"""
OpenAI provider — cloud model (GPT) for demanding requests.

Setup:
    Requires an API key from https://platform.openai.com/api-keys
    (a developer key, billed by usage — NOT your ChatGPT Plus login).
    Set OPENAI_API_KEY in config/.env.

Design choice:
    Uses the official `openai` Python SDK rather than raw HTTP calls,
    since OpenAI maintains it and it handles retries/edge cases we'd
    otherwise have to reimplement.
"""

from openai import AsyncOpenAI, APIConnectionError, AuthenticationError, OpenAIError

from backend.ai.base import AIResponse, Message, ProviderUnavailableError
from backend.core.config import settings
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        self.model = DEFAULT_MODEL
        self._client: AsyncOpenAI | None = None
        if settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def is_available(self) -> bool:
        return self._client is not None

    async def generate(self, messages: list[Message]) -> AIResponse:
        if self._client is None:
            raise ProviderUnavailableError(
                "OPENAI_API_KEY is not set in config/.env"
            )

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
            )
        except AuthenticationError as exc:
            raise ProviderUnavailableError(
                "OpenAI rejected the API key — check OPENAI_API_KEY in config/.env"
            ) from exc
        except APIConnectionError as exc:
            raise ProviderUnavailableError(
                "Could not connect to OpenAI — check your internet connection"
            ) from exc
        except OpenAIError as exc:
            raise ProviderUnavailableError(f"OpenAI API error: {exc}") from exc

        choice = response.choices[0]
        usage = response.usage

        return AIResponse(
            text=choice.message.content or "",
            provider_name=self.name,
            model_name=self.model,
            input_tokens=usage.prompt_tokens if usage else None,
            output_tokens=usage.completion_tokens if usage else None,
        )
