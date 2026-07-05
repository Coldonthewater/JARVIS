"""Tests for backend/gateway/auth.py — token verification."""

import pytest

from backend.gateway.auth import AuthConfigurationError, InvalidTokenError, verify_token


def test_missing_configured_token_raises_configuration_error(monkeypatch):
    monkeypatch.setattr("backend.gateway.auth.settings.gateway_auth_token", None)
    with pytest.raises(AuthConfigurationError):
        verify_token("anything")


def test_correct_token_passes(monkeypatch):
    monkeypatch.setattr("backend.gateway.auth.settings.gateway_auth_token", "secret123")
    verify_token("secret123")  # should not raise


def test_incorrect_token_raises_invalid_token_error(monkeypatch):
    monkeypatch.setattr("backend.gateway.auth.settings.gateway_auth_token", "secret123")
    with pytest.raises(InvalidTokenError):
        verify_token("wrong-token")


def test_missing_presented_token_raises_invalid_token_error(monkeypatch):
    monkeypatch.setattr("backend.gateway.auth.settings.gateway_auth_token", "secret123")
    with pytest.raises(InvalidTokenError):
        verify_token(None)
