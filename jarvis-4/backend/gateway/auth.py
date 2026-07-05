"""
Gateway authentication — verifies the bearer token every client must
send.

Why this exists:
    The moment the gateway is reachable beyond localhost (LAN, or via
    Tailscale from your phone/MacBook), it needs real authentication —
    not "add it later." This is intentionally simple: one shared,
    long-lived token, not full OAuth. OAuth belongs at the integration
    layer (Module 5), where Jarvis authenticates to external services
    like Google/Microsoft on your behalf. This token is the reverse:
    it's how a client proves to Jarvis that it's allowed to connect.

Design choice:
    A single static token is the right level of complexity for a
    personal system with a handful of your own devices. If Jarvis ever
    needs per-device revocation (e.g. "revoke just my old phone"), this
    is the file to upgrade to per-client tokens — the interface
    (`verify_token`) won't need to change for callers.
"""

import hmac

from backend.core.config import settings
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)


class AuthConfigurationError(Exception):
    """Raised when the gateway is asked to authenticate but no token is configured."""


class InvalidTokenError(Exception):
    """Raised when a client presents a token that doesn't match."""


def verify_token(presented_token: str | None) -> None:
    """
    Verifies a client-presented token against the configured gateway
    token. Raises on failure; callers (REST middleware, WebSocket
    handshake) decide how to translate that into an HTTP/WS error.

    Uses `hmac.compare_digest` instead of `==` to avoid leaking timing
    information about how much of the token matched — standard
    practice for comparing secrets.
    """
    if not settings.gateway_auth_token:
        raise AuthConfigurationError(
            "GATEWAY_AUTH_TOKEN is not set in config/.env. Set one before "
            "allowing any client (including localhost tools) to connect."
        )

    if not presented_token or not hmac.compare_digest(
        presented_token, settings.gateway_auth_token
    ):
        raise InvalidTokenError("Invalid or missing gateway auth token")
