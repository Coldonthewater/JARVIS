"""
WebSocket route — real-time chat over a persistent connection.

Why this exists alongside the REST /chat endpoint:
    REST is simplest for a one-off message. WebSocket is what future
    features need: streaming tokens as the AI generates them, and
    pushing events (notifications, status changes) to a client without
    it having to poll. This route proves the WebSocket path works
    end-to-end for chat; streaming token-by-token and pushing
    non-chat events will build on this same connection in later
    modules.

Auth over WebSocket:
    Standard WebSocket connections can't send custom headers from a
    browser easily, so the token is passed as a query parameter
    instead: `ws://host:port/ws/chat?token=...`. This is a common,
    accepted pattern for WebSocket auth (the alternative, an
    in-band auth message after connecting, adds a handshake step for
    marginal benefit in this context).
"""

from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.ai.conversation import Conversation
from backend.ai.engine import AllProvidersUnavailableError, ai_engine
from backend.core.logging_setup import get_logger
from backend.gateway.auth import AuthConfigurationError, InvalidTokenError, verify_token
from backend.gateway.ws.connection_manager import connection_manager

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket, token: str | None = None) -> None:
    try:
        verify_token(token)
    except (AuthConfigurationError, InvalidTokenError) as exc:
        # Must accept before closing with a reason, per the ASGI/WebSocket spec.
        await websocket.accept()
        await websocket.close(code=4401, reason=str(exc))
        return

    client_id = str(uuid4())
    await connection_manager.connect(client_id, websocket)
    conversation = Conversation()

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            if not user_message:
                continue

            try:
                result = await ai_engine.respond(conversation, user_message)
                await connection_manager.send_json(
                    client_id,
                    {
                        "type": "chat_response",
                        "reply": result.text,
                        "provider": result.provider_name,
                        "model": result.model_name,
                        "category": result.category,
                        "routed_local": result.routed_local,
                        "escalated_for_confidence": result.escalated_for_confidence,
                    },
                )
            except AllProvidersUnavailableError as exc:
                await connection_manager.send_json(
                    client_id, {"type": "error", "message": str(exc)}
                )
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
