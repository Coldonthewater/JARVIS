"""Tests for backend/core/config.py — localhost-only enforcement."""

import warnings

from backend.core.config import Settings


def test_gateway_host_defaults_to_localhost():
    s = Settings(_env_file=None)
    assert s.gateway_host == "127.0.0.1"


def test_gateway_host_override_is_forced_back_to_localhost():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s = Settings(_env_file=None, gateway_host="0.0.0.0")

    assert s.gateway_host == "127.0.0.1"
    assert any("cross-device access is currently disabled" in str(w.message) for w in caught)
