"""
Tests for backend/ai/engine.py — fallback behavior and confidence-based
escalation from local to cloud.

We use small fake providers instead of real API calls, both so tests
run without network access / API keys, and so we can deliberately
simulate a provider being unavailable or giving an uncertain answer.
"""

import pytest

from backend.ai.base import AIResponse, Message, ProviderUnavailableError
from backend.ai.conversation import Conversation
from backend.ai.engine import AIEngine, AllProvidersUnavailableError


class FakeWorkingProvider:
    """A provider that always succeeds with a fixed response."""

    def __init__(self, name: str, response_text: str = "fake response") -> None:
        self.name = name
        self.response_text = response_text

    async def is_available(self) -> bool:
        return True

    async def generate(self, messages: list[Message]) -> AIResponse:
        return AIResponse(text=self.response_text, provider_name=self.name, model_name="fake-model")


class FakeBrokenProvider:
    """A provider that always fails, simulating e.g. a missing API key or offline local model."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def is_available(self) -> bool:
        return False

    async def generate(self, messages: list[Message]) -> AIResponse:
        raise ProviderUnavailableError(f"{self.name} is not configured")


@pytest.fixture
def engine() -> AIEngine:
    e = AIEngine()
    e._providers = {
        "working": FakeWorkingProvider("working"),
        "broken": FakeBrokenProvider("broken"),
    }
    return e


@pytest.mark.asyncio
async def test_primary_provider_succeeds_no_fallback_needed(engine, monkeypatch):
    monkeypatch.setattr("backend.ai.engine.settings.ai_local_provider", "working")
    monkeypatch.setattr("backend.ai.engine.settings.ai_fallback_provider", "broken")

    conversation = Conversation()
    # "hi there" defaults to everyday_conversation -> LOCAL -> uses ai_local_provider
    response = await engine.respond(conversation, "hi there")

    assert response.provider_name == "working"


@pytest.mark.asyncio
async def test_falls_back_when_primary_provider_unavailable(engine, monkeypatch):
    monkeypatch.setattr("backend.ai.engine.settings.ai_local_provider", "broken")
    monkeypatch.setattr("backend.ai.engine.settings.ai_fallback_provider", "working")

    conversation = Conversation()
    response = await engine.respond(conversation, "hi there")

    assert response.provider_name == "working"


@pytest.mark.asyncio
async def test_raises_when_both_primary_and_fallback_unavailable(engine, monkeypatch):
    engine._providers["also_broken"] = FakeBrokenProvider("also_broken")
    monkeypatch.setattr("backend.ai.engine.settings.ai_local_provider", "broken")
    monkeypatch.setattr("backend.ai.engine.settings.ai_fallback_provider", "also_broken")

    conversation = Conversation()
    with pytest.raises(AllProvidersUnavailableError):
        await engine.respond(conversation, "hi there")


@pytest.mark.asyncio
async def test_conversation_history_updated_after_response(engine, monkeypatch):
    monkeypatch.setattr("backend.ai.engine.settings.ai_local_provider", "working")

    conversation = Conversation()
    await engine.respond(conversation, "hello")

    roles = [m.role for m in conversation.messages]
    assert roles[-2:] == ["user", "assistant"]
    assert conversation.messages[-1].content == "fake response"


@pytest.mark.asyncio
async def test_uncertain_local_response_escalates_to_cloud(engine, monkeypatch):
    engine._providers["working"] = FakeWorkingProvider(
        "working", response_text="I'm not sure, but maybe around 3pm?"
    )
    engine._providers["cloud"] = FakeWorkingProvider("cloud", response_text="It's at 3pm.")
    monkeypatch.setattr("backend.ai.engine.settings.ai_local_provider", "working")
    monkeypatch.setattr("backend.ai.engine.settings.ai_cloud_provider", "cloud")

    conversation = Conversation()
    # "hi there" is UNKNOWN -> LOCAL tier, so it hits the uncertain local
    # provider first, then should escalate to the cloud provider.
    response = await engine.respond(conversation, "hi there")

    assert response.provider_name == "cloud"
    assert response.text == "It's at 3pm."


@pytest.mark.asyncio
async def test_confident_local_response_does_not_escalate(engine, monkeypatch):
    engine._providers["working"] = FakeWorkingProvider(
        "working", response_text="It's sunny and 75 degrees."
    )
    engine._providers["cloud"] = FakeWorkingProvider("cloud", response_text="should not be used")
    monkeypatch.setattr("backend.ai.engine.settings.ai_local_provider", "working")
    monkeypatch.setattr("backend.ai.engine.settings.ai_cloud_provider", "cloud")

    conversation = Conversation()
    response = await engine.respond(conversation, "what's the weather")

    assert response.provider_name == "working"


@pytest.mark.asyncio
async def test_code_request_routes_directly_to_cloud(engine, monkeypatch):
    engine._providers["working"] = FakeWorkingProvider("working", response_text="should not be used")
    engine._providers["cloud"] = FakeWorkingProvider("cloud", response_text="here's your function")
    monkeypatch.setattr("backend.ai.engine.settings.ai_local_provider", "working")
    monkeypatch.setattr("backend.ai.engine.settings.ai_cloud_provider", "cloud")

    conversation = Conversation()
    response = await engine.respond(conversation, "write a python function to sort a list")

    assert response.provider_name == "cloud"
