"""Tests for backend/gateway/client_registry.py."""

from backend.gateway.client_registry import ClientCapabilities, ClientRegistry


def test_register_returns_unique_client_id():
    registry = ClientRegistry()
    id_a = registry.register(ClientCapabilities(client_type="desktop"))
    id_b = registry.register(ClientCapabilities(client_type="mobile"))
    assert id_a != id_b


def test_registered_client_is_retrievable():
    registry = ClientRegistry()
    client_id = registry.register(ClientCapabilities(client_type="wall_display", has_display=True))
    client = registry.get(client_id)
    assert client is not None
    assert client.capabilities.client_type == "wall_display"
    assert client.capabilities.has_display is True


def test_unregister_removes_client():
    registry = ClientRegistry()
    client_id = registry.register(ClientCapabilities())
    registry.unregister(client_id)
    assert registry.get(client_id) is None


def test_all_clients_lists_every_registered_client():
    registry = ClientRegistry()
    registry.register(ClientCapabilities(client_type="desktop"))
    registry.register(ClientCapabilities(client_type="mobile"))
    assert len(registry.all_clients()) == 2
