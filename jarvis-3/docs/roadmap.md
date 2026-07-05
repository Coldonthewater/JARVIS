# Jarvis — Roadmap

_This is a living document. Update it as modules are completed or the plan changes._

## Phase Plan

| # | Module | Status | Summary |
|---|---|---|---|
| 1 | Core Backend | ✅ Complete | Config system, logging, event bus, entry point |
| 2 | AI Brain | ✅ Complete | Hybrid local/cloud routing across Ollama, OpenAI, Gemini, Anthropic |
| 3 | Gateway | ⬜ Next | REST + WebSocket API, client registry, capability negotiation, auth |
| 4 | Memory | ⬜ Planned | Local database, conversation history, preferences |
| 5 | Integrations | ⬜ Planned | Plugin interface proven with 2–3 real services (e.g. Weather, Spotify, Calendar) |
| 6 | Voice | ⬜ Planned | Wake word → STT → AI → TTS pipeline |
| 7 | Desktop Dashboard | ⬜ Planned | First real client (Electron + React) |
| 8 | Additional Clients | ⬜ Planned | Mobile, wall display, etc. |
| 9 | Smart Home | ⬜ Planned | Home Assistant, Philips Hue, smart plugs |
| 10 | Security Hardening | ⬜ Planned | OAuth flows, credential vault, revocation UI |
| 11 | Polish | ⬜ Planned | Multiple voices, interruption handling, push-to-talk, local AI option |

## Module 2 — What was built

- `backend/ai/base.py` — the `AIProvider` interface every provider adapter implements (`Protocol`-based)
- `backend/ai/providers/` — adapters for Ollama (local), OpenAI, Gemini, and Anthropic — each isolates its own SDK quirks
- `backend/ai/router.py` — category-based classifier: everyday conversation, app control, smart home, weather, memory, and automation route local; code, planning, research, and summarization route cloud; local responses that read as unconfident auto-escalate to cloud
- `backend/ai/conversation.py` — in-memory message history (will move to the database in Module 4)
- `backend/ai/engine.py` — orchestrates routing + provider calls + confidence-based escalation + automatic fallback if the chosen provider is unavailable
- `backend/main.py` — now includes a terminal chat loop to manually test the AI engine
- `backend/tests/test_router.py`, `backend/tests/test_engine.py` — classifier tests + fallback-behavior tests using fake providers (no API keys needed to run tests)

### Design notes worth remembering

- **Any provider can be added** by writing one adapter file implementing `AIProvider` and adding one line to `engine.py`'s registry — no other code changes.
- **Routing is currently rule-based** (keywords + message length). This is a deliberate placeholder — see `future-features.md` for a smarter classifier idea.
- **Fallback is automatic**: if the local model isn't running, or a cloud key is missing/invalid, the engine escalates to the configured fallback provider rather than failing the request.
- Cloud provider keys are **developer API keys**, billed by usage — not the same as ChatGPT Plus / Gemini Advanced subscriptions.

## Next up — Module 3: Gateway

Goal: REST + WebSocket API in front of the AI engine, with a client
registry and capability negotiation so any future client (desktop,
mobile, wall display, AR glasses) can connect the same way. Since you
want remote access from a Windows "home base" to other devices, this
module will also need to address authentication and network exposure
(likely via Tailscale) — not just localhost.
