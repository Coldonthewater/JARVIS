"""
Ollama provider — runs a model locally on this machine (or LAN).

Why this exists:
    This is the "simple requests" leg of the hybrid design. Ollama runs
    open-source models (e.g. Llama 3.1) locally, with zero API cost and
    no data leaving the machine. It's ideal for quick, low-stakes
    requests, but generally less capable than the large cloud models.

Setup (not required to run Jarvis, but required for this provider):
    1. Install Ollama: https://ollama.com
    2. Run: ollama pull llama3.1   (or whichever model you configure)
    3. Ollama runs a local server automatically — no API key needed.

Design choice:
    We call Ollama's local HTTP API directly with `httpx` rather than
    a dedicated SDK — it's a very thin API and avoids an extra
    dependency for something this simple.
"""

import httpx

from backend.ai.base import AIResponse, Message, ProviderUnavailableError
from backend.core.config import settings
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)


class OllamaProvider:
    name = "ollama"

    def __init__(self) -> None:
        self.host = settings.ollama_host.rstrip("/")
        self.model = settings.ollama_model

    async def is_available(self) -> bool:
        """Pings the local Ollama server. Returns False if it's not running."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.host}/api/tags")
                return response.status_code == 200
        except httpx.RequestError:
            return False

    async def generate(self, messages: list[Message]) -> AIResponse:
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self.host}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as exc:
            raise ProviderUnavailableError(
                f"Could not reach Ollama at {self.host}. "
                f"Is Ollama running? (`ollama serve`, or check it's installed)"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(
                f"Ollama returned an error: {exc.response.text}"
            ) from exc

        return AIResponse(
            text=data["message"]["content"],
            provider_name=self.name,
            model_name=self.model,
            # Ollama reports token counts differently across versions;
            # left as None here rather than guessing at the field name.
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
        )
