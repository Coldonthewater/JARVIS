"""
WebSocket connection manager — tracks active WebSocket connections
separately from the client registry.

Why separate from ClientRegistry:
    A client can be "registered" (has declared capabilities) without
    currently holding an open WebSocket — e.g. it registered via REST
    and is only polling. This manager tracks the live socket objects
    needed to actually push data to a connection, which is a distinct
    concern from capability bookkeeping.
"""

from fastapi import WebSocket

from backend.core.logging_setup import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str) -> None:
        if client_id in self._connections:
            del self._connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_json(self, client_id: str, data: dict) -> None:
        websocket = self._connections.get(client_id)
        if websocket is not None:
            await websocket.send_json(data)


# Application-wide singleton, same pattern as client_registry.
connection_manager = ConnectionManager()
