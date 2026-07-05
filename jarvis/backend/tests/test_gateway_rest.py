"""
Tests for the REST gateway (backend/gateway/rest/).

Uses FastAPI's TestClient (built on httpx) to exercise routes without
actually binding a network port. The AI engine call in /chat is
monkeypatched so this test doesn't require a real provider or API key.
"""

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from backend.gateway.rest.app import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("backend.gateway.rest.routes.settings.gateway_auth_token", "test-token")
    app = create_app()
    return TestClient(app)


def test_health_check_requires_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_without_token_is_rejected(client):
    response = client.post("/chat", json={"message": "hi"})
    assert response.status_code == 401


def test_chat_with_wrong_token_is_rejected(client):
    response = client.post(
        "/chat", json={"message": "hi"}, headers={"Authorization": "Bearer wrong"}
    )
    assert response.status_code == 401


def test_chat_with_correct_token_succeeds(client, monkeypatch):
    @dataclass
    class FakeResult:
        text: str = "hello back"
        provider_name: str = "fake"
        model_name: str = "fake-model"
        category: str = "everyday_conversation"
        routed_local: bool = True
        escalated_for_confidence: bool = False

    async def fake_respond(conversation, message, **kwargs):
        return FakeResult()

    monkeypatch.setattr("backend.gateway.rest.routes.ai_engine.respond", fake_respond)

    response = client.post(
        "/chat",
        json={"message": "hi"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "hello back"
    assert body["provider"] == "fake"
    assert "conversation_id" in body


def test_register_client_with_correct_token_succeeds(client):
    response = client.post(
        "/clients/register",
        json={"client_type": "desktop", "has_display": True},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert "client_id" in response.json()
