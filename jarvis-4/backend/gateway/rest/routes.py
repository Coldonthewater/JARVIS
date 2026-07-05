"""
REST routes — health check, client registration, chat, and memory
(preferences, rooms, devices, automations, notes).

Why chat is REST (not only WebSocket):
    A simple request/response chat call is easier for many clients to
    implement than a WebSocket connection, and doesn't require holding
    a persistent connection open. The WebSocket route (ws/routes.py)
    exists for clients that want streaming or real-time events. Both
    ultimately call the same conversation_service, which itself calls
    `ai_engine.respond(...)` — this is the payoff of routing all
    reasoning through one engine module.

Conversation storage:
    As of Module 4, conversation history is persisted via
    backend.gateway.conversation_service (backed by the database) —
    it survives a backend restart. The Module 3 in-memory placeholder
    dict has been removed.
"""

from fastapi import APIRouter, Header, HTTPException

from backend.ai.engine import AllProvidersUnavailableError
from backend.core.config import settings
from backend.core.logging_setup import get_logger
from backend.gateway.auth import AuthConfigurationError, InvalidTokenError, verify_token
from backend.gateway.client_registry import ClientCapabilities, client_registry
from backend.gateway.conversation_service import get_or_create_conversation_id, send_message
from backend.gateway.rest.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    PreferenceRequest,
    PreferenceResponse,
    RegisterClientRequest,
    RegisterClientResponse,
)
from backend.memory.repositories.preference_repository import preference_repository

logger = get_logger(__name__)
router = APIRouter()


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

    conversation_id = await get_or_create_conversation_id(body.conversation_id)

    try:
        result = await send_message(conversation_id, body.message)
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


@router.get("/memory/preferences", response_model=dict[str, str])
async def list_preferences(authorization: str | None = Header(default=None)) -> dict[str, str]:
    _require_auth(authorization)
    return await preference_repository.list_all()


@router.put("/memory/preferences/{key}", response_model=PreferenceResponse)
async def set_preference(
    key: str, body: PreferenceRequest, authorization: str | None = Header(default=None)
) -> PreferenceResponse:
    _require_auth(authorization)
    await preference_repository.set(key, body.value)
    return PreferenceResponse(key=key, value=body.value)


@router.delete("/memory/preferences/{key}")
async def delete_preference(key: str, authorization: str | None = Header(default=None)) -> dict[str, str]:
    _require_auth(authorization)
    await preference_repository.delete(key)
    return {"status": "deleted", "key": key}
