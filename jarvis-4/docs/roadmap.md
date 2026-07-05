# Jarvis — Roadmap

_This is a living document. Update it as modules are completed or the plan changes._

## Phase Plan

| # | Module | Status | Summary |
|---|---|---|---|
| 1 | Core Backend | ✅ Complete | Config system, logging, event bus, entry point |
| 2 | AI Brain | ✅ Complete | Hybrid local/cloud routing across Ollama, OpenAI, Gemini, Anthropic |
| 3 | Gateway | ✅ Complete | REST + WebSocket API, client registry, token auth, remote-access ready |
| 4 | Memory | ✅ Complete | Local SQLite database, persisted conversations, preferences, rooms, devices, automations, notes |
| 5 | Integrations | ⬜ Next | Plugin interface proven with 2–3 real services (e.g. Weather, Spotify, Calendar) |
| 6 | Voice | ⬜ Planned | Wake word → STT → AI → TTS pipeline |
| 7 | Desktop Dashboard | ⬜ Planned | First real client (Electron + React) |
| 8 | Additional Clients | ⬜ Planned | Mobile, wall display, etc. |
| 9 | Smart Home | ⬜ Planned | Home Assistant, Philips Hue, smart plugs |
| 10 | Security Hardening | ⬜ Planned | OAuth flows, credential vault, revocation UI |
| 11 | Polish | ⬜ Planned | Multiple voices, interruption handling, push-to-talk, local AI option |

## Module 3 — What was built

- `backend/gateway/auth.py` — bearer token verification, shared by REST and WebSocket
- `backend/gateway/client_registry.py` — in-memory registry of connected clients and declared capabilities (mic, speaker, display, push notifications) — enables any future client type to connect with zero backend changes
- `backend/gateway/rest/` — FastAPI app (`app.py`), routes (`/health`, `/clients/register`, `/chat`), and schemas
- `backend/gateway/ws/` — WebSocket chat endpoint (`/ws/chat`) and connection manager
- `backend/ai/engine.py` — `respond()` now returns `EngineResult` (text + category, routed_local, escalated_for_confidence) so the gateway can expose routing details to clients
- `backend/main.py` — now starts the gateway (`uvicorn`) by default; `--chat` still runs the Module 2 terminal loop for quick testing
- New tests: `test_gateway_auth.py`, `test_client_registry.py`, `test_gateway_rest.py`

### Design notes worth remembering

- **Auth is a single shared bearer token** (`GATEWAY_AUTH_TOKEN`), not OAuth — OAuth is reserved for Module 5, where Jarvis authenticates *to* external services on your behalf. This token is the reverse: proof a client is allowed to talk to Jarvis.
- **Gateway is localhost-only by design** — cross-device access was deferred (see `docs/future-features.md`).
- API docs auto-generate at `/docs` once the gateway is running.

## Module 4 — What was built

- `backend/memory/models.py` — SQLAlchemy ORM schema: `Conversation`, `StoredMessage`, `Preference`, `Room`, `Device`, `AutomationRule`, `Note`
- `backend/memory/database.py` — async SQLite engine/session setup (`aiosqlite`), `init_db()` creates tables on first run
- `backend/memory/repositories/` — `conversation_repository.py`, `preference_repository.py`, `household_repository.py` (rooms, devices, automations, notes) — the only files that touch the ORM directly
- `backend/ai/conversation.py` — added `Conversation.from_history()` so persisted messages can rehydrate a conversation without duplicating the system prompt
- `backend/gateway/conversation_service.py` — shared by REST and WebSocket: loads history, calls the AI engine, persists both turns. Replaces the Module 3 in-memory conversation dict.
- REST additions: `GET/PUT/DELETE /memory/preferences` for reading/writing remembered preferences
- WebSocket: `/ws/chat` now accepts `?conversation_id=...` to resume a persisted conversation
- New tests: `test_conversation_repository.py`, `test_preference_repository.py`, `test_household_repository.py`, `test_conversation_service.py`, plus a shared `conftest.py` fixture (`memory_db`) that gives every test an isolated in-memory database

### Design notes worth remembering

- **SQLite for now, Postgres later if ever needed** — `database.py` is the only file that would need to change; every repository is built on SQLAlchemy's ORM, not raw SQL.
- **`create_all()`, not migrations** — appropriate while the schema is still moving fast this early. Revisit with Alembic once it stabilizes (tracked in `docs/future-features.md`) so future schema changes don't risk data loss.
- **Preferences are a generic key-value store**, not a fixed schema — the range of things Jarvis might remember is open-ended and will keep growing with new integrations.
- **Rooms/devices/automations/notes have REST endpoints deferred** — models and repositories exist and are tested now, but CRUD endpoints for these will be added when Module 5 (integrations) or the dashboard actually needs to read/write them, to avoid building API surface nothing calls yet.
- The terminal `--chat` mode from Module 2 intentionally stays pure in-memory (not persisted) — it's a dev/testing shortcut, not the primary interface.

## Next up — Module 5: Integrations

Goal: prove the plugin-based `Integration` interface with 2–3 real
services (candidates: Weather, Spotify, Calendar). This is also where
OAuth enters the picture — for Jarvis authenticating *to* these
services on your behalf, distinct from the gateway's own auth token.
