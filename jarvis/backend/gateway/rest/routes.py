"""
REST routes — health check, client registration, and chat.

Why chat is REST (not only WebSocket):
    A simple request/response chat call is easier for many clients to
    implement than a WebSocket connection, and doesn't require holding
    a persistent connection open. The WebSocket route (ws/routes.py)
    exists for clients that want streaming or real-time events. Both
    ultimately call the same `ai_engine.respond(...)` — this is the
    payoff of routing all reasoning through one engine module.

Conversation storage note:
    This module keeps an in-memory dict of conversation_id ->
    Conversation, purely to let a client send multiple chat messages
    that build on each other within one run of the backend. This is a
    placeholder — Module 4 (Memory) will persist conversations properly
    and this dict will be replaced.
"""

from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException

from backend.ai.conversation import Conversation
from backend.ai.engine import AllProvidersUnavailableError, ai_engine
from backend.core.config import settings
from backend.gateway.auth import AuthConfigurationError, InvalidTokenError, verify_token
from backend.gateway.client_registry import ClientCapabilities, client_registry
from backend.gateway.rest.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    RegisterClientRequest,
    RegisterClientResponse,
)
from backend.core.logging_setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Placeholder in-memory conversation store — see module docstring.
_conversations: dict[str, Conversation] = {}


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.removeprefix("Bearer ").strip()


def _require_auth(authorization: str | None = Header(default=None)) -> None:
    """FastAPI dependency — add `_: None = Depends(_require_auth)` to any route that needs auth."""
    token = _extract_bearer_token(authorization)
    try:
        verify_token(token)
    except AuthConfigurationError as exc:
        # Server misconfiguration, not the client's fault — 500, not 401.
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Unauthenticated on purpose — lets a client (or you, debugging)
    confirm the gateway is up before worrying about tokens.
    """
    return HealthResponse(status="ok", app_name=settings.app_name, environment=settings.environment)


@router.post("/clients/register", response_model=RegisterClientResponse)
async def register_client(
    body: RegisterClientRequest, authorization: str | None = Header(default=None)
) -> RegisterClientResponse:
    _require_auth(authorization)

    capabilities = ClientCapabilities(
        client_type=body.client_type,
        has_microphone=body.has_microphone,
        has_speaker=body.has_speaker,
        has_display=body.has_display,
        supports_push_notifications=body.supports_push_notifications,
    )
    client_id = client_registry.register(capabilities)
    return RegisterClientResponse(client_id=client_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, authorization: str | None = Header(default=None)
) -> ChatResponse:
    _require_auth(authorization)

    conversation_id = body.conversation_id or str(uuid4())
    conversation = _conversations.setdefault(conversation_id, Conversation())

    try:
        result = await ai_engine.respond(conversation, body.message)
    except AllProvidersUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No AI provider could handle this request: {exc}",
        ) from exc

    return ChatResponse(
        conversation_id=conversation_id,
        reply=result.text,
        provider=result.provider_name,
        model=result.model_name,
        category=result.category,
        routed_local=result.routed_local,
        escalated_for_confidence=result.escalated_for_confidence,
    )
