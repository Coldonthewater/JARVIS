"""
FastAPI application factory for the gateway.

Why a factory function instead of a module-level app:
    Building the app via a function (`create_app()`) rather than a bare
    module-level `app = FastAPI()` makes it easy to construct
    differently configured instances later (e.g. a test app with
    different settings) without import-time side effects. FastAPI's
    own docs recommend this pattern for anything beyond a toy project.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.logging_setup import get_logger
from backend.gateway.rest.routes import router as rest_router
from backend.gateway.ws.routes import router as ws_router
from backend.memory.database import init_db

logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Jarvis Gateway",
        description="The single API surface every Jarvis client (desktop, mobile, wall display, AR) connects through.",
        version="0.4.0",  # tracks module number loosely, not semver strictly yet
    )

    # CORS: permissive for now since clients are all first-party devices
    # you control, not arbitrary third-party websites. Revisit if/when
    # a browser-based client is added, to scope this down.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(rest_router)
    app.include_router(ws_router)

    @app.on_event("startup")
    async def _on_startup() -> None:
        logger.info(
            f"Gateway starting on {settings.gateway_host}:{settings.gateway_port} "
            f"(localhost-only, environment={settings.environment})"
        )
        if not settings.gateway_auth_token:
            logger.warning(
                "GATEWAY_AUTH_TOKEN is not set — every request will be rejected. "
                "Re-run `python -m backend.setup` or set one in config/.env."
            )
        await init_db()

    return app
