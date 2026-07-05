"""
Gemini provider — Google's cloud model, for demanding requests.

Setup:
    Requires an API key from Google AI Studio: https://aistudio.google.com/apikey
    (a developer key, billed by usage — NOT your Gemini Advanced login).
    Set GOOGLE_API_KEY in config/.env.

Design choice:
    Uses Google's official `google-genai` SDK. Like the OpenAI adapter,
    all Gemini-specific request/response shaping happens only in this
    file — the rest of Jarvis never sees it.
"""

from google import genai
from google.genai.errors import APIError

from backend.ai.base import AIResponse, Message, ProviderUnavailableError
from backend.core.config import settings
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider:
    name = "gemini"

    def __init__(self) -> None:
        self.model = DEFAULT_MODEL
        self._client: genai.Client | None = None
        if settings.google_api_key:
            self._client = genai.Client(api_key=settings.google_api_key)

    async def is_available(self) -> bool:
        return self._client is not None

    async def generate(self, messages: list[Message]) -> AIResponse:
        if self._client is None:
            raise ProviderUnavailableError(
                "GOOGLE_API_KEY is not set in config/.env"
            )

        # Gemini separates the system prompt from the conversation turns,
        # and uses "model" instead of "assistant" as the role name — this
        # translation stays local to this file.
        system_instruction = "\n".join(m.content for m in messages if m.role == "system")
        contents = [
            {
                "role": "model" if m.role == "assistant" else "user",
                "parts": [{"text": m.content}],
            }
            for m in messages
            if m.role != "system"
        ]

        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config={"system_instruction": system_instruction} if system_instruction else None,
            )
        except APIError as exc:
            raise ProviderUnavailableError(f"Gemini API error: {exc}") from exc

        usage = getattr(response, "usage_metadata", None)

        return AIResponse(
            text=response.text or "",
            provider_name=self.name,
            model_name=self.model,
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
        )
