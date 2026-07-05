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
def client(monkeypatch, memory_db):
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

    monkeypatch.setattr(
        "backend.gateway.conversation_service.ai_engine.respond", fake_respond
    )

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


def test_chat_persists_across_requests_with_same_conversation_id(client, monkeypatch):
    @dataclass
    class FakeResult:
        text: str = "response"
        provider_name: str = "fake"
        model_name: str = "fake-model"
        category: str = "everyday_conversation"
        routed_local: bool = True
        escalated_for_confidence: bool = False

    seen_history_lengths = []

    async def fake_respond(conversation, message, **kwargs):
        seen_history_lengths.append(len(conversation.messages))
        return FakeResult()

    monkeypatch.setattr(
        "backend.gateway.conversation_service.ai_engine.respond", fake_respond
    )

    headers = {"Authorization": "Bearer test-token"}
    first = client.post("/chat", json={"message": "first"}, headers=headers)
    conversation_id = first.json()["conversation_id"]

    client.post(
        "/chat",
        json={"message": "second", "conversation_id": conversation_id},
        headers=headers,
    )

    assert seen_history_lengths[1] > seen_history_lengths[0]


def test_preference_set_get_and_delete(client):
    headers = {"Authorization": "Bearer test-token"}

    set_response = client.put(
        "/memory/preferences/favorite_color", json={"value": "teal"}, headers=headers
    )
    assert set_response.status_code == 200

    list_response = client.get("/memory/preferences", headers=headers)
    assert list_response.json()["favorite_color"] == "teal"

    delete_response = client.delete("/memory/preferences/favorite_color", headers=headers)
    assert delete_response.status_code == 200

    list_after_delete = client.get("/memory/preferences", headers=headers)
    assert "favorite_color" not in list_after_delete.json()


def test_register_client_with_correct_token_succeeds(client):
    response = client.post(
        "/clients/register",
        json={"client_type": "desktop", "has_display": True},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    assert "client_id" in response.json()
