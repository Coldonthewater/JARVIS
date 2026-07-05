# Jarvis — Roadmap

_This is a living document. Update it as modules are completed or the plan changes._

## Phase Plan

| # | Module | Status | Summary |
|---|---|---|---|
| 1 | Core Backend | ✅ Complete | Config system, logging, event bus, entry point |
| 2 | AI Brain | ✅ Complete | Hybrid local/cloud routing across Ollama, OpenAI, Gemini, Anthropic |
| 3 | Gateway | ✅ Complete | REST + WebSocket API, client registry, token auth, remote-access ready |
| 4 | Memory | ⬜ Next | Local database, conversation history, preferences |
| 5 | Integrations | ⬜ Planned | Plugin interface proven with 2–3 real services (e.g. Weather, Spotify, Calendar) |
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
- **Gateway defaults to localhost-only.** To reach it from your MacBook/phone, install **Tailscale** on both devices and connect via the Tailscale IP — safer than opening the raw LAN/router. See `docs/architecture.md`.
- **Conversation storage in the gateway is still in-memory** — a placeholder until Module 4 adds real persistence.
- API docs auto-generate at `/docs` once the gateway is running.

## Next up — Module 4: Memory

Goal: a local database for conversation history, user preferences,
devices, rooms, and automation rules — replacing the gateway's
in-memory conversation dict with real persistence, and giving the AI
engine access to remembered preferences for the `memory_preference`
routing category.
