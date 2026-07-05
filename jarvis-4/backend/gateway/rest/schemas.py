"""
Request/response schemas for the REST API.

Why a separate file:
    Keeping these separate from the route handlers means the "shape"
    of the API is easy to see at a glance, and these same models double
    as the source of FastAPI's auto-generated OpenAPI schema — which
    is what future clients (mobile, wall display) will code against.
"""

from pydantic import BaseModel, Field


class RegisterClientRequest(BaseModel):
    client_type: str = Field(
        default="unknown",
        description="Free-form label, e.g. 'desktop', 'mobile', 'wall_display', 'ar_glasses'",
    )
    has_microphone: bool = False
    has_speaker: bool = False
    has_display: bool = False
    supports_push_notifications: bool = False


class RegisterClientResponse(BaseModel):
    client_id: str


class ChatRequest(BaseModel):
    message: str
    # Optional — omit to start a new conversation. In Module 4, this
    # will map to a conversation persisted in the database; for now it
    # only distinguishes conversations held in memory for this run.
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    provider: str
    model: str
    category: str
    routed_local: bool
    escalated_for_confidence: bool


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str


class PreferenceRequest(BaseModel):
    value: str


class PreferenceResponse(BaseModel):
    key: str
    value: str
