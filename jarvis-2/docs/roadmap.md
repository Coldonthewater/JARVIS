# Jarvis — Roadmap

_This is a living document. Update it as modules are completed or the plan changes._

## Phase Plan

| # | Module | Status | Summary |
|---|---|---|---|
| 1 | Core Backend | ✅ Complete | Config system, logging, event bus, entry point |
| 2 | AI Brain | ⬜ Next | Claude integration behind a reasoning abstraction so local models can be swapped in later |
| 3 | Gateway | ⬜ Planned | REST + WebSocket API, client registry, capability negotiation, auth |
| 4 | Memory | ⬜ Planned | Local database, conversation history, preferences |
| 5 | Integrations | ⬜ Planned | Plugin interface proven with 2–3 real services (e.g. Weather, Spotify, Calendar) |
| 6 | Voice | ⬜ Planned | Wake word → STT → AI → TTS pipeline |
| 7 | Desktop Dashboard | ⬜ Planned | First real client (Electron + React) |
| 8 | Additional Clients | ⬜ Planned | Mobile, wall display, etc. |
| 9 | Smart Home | ⬜ Planned | Home Assistant, Philips Hue, smart plugs |
| 10 | Security Hardening | ⬜ Planned | OAuth flows, credential vault, revocation UI |
| 11 | Polish | ⬜ Planned | Multiple voices, interruption handling, push-to-talk, local AI option |

## Module 1 — What was built

- `backend/core/config.py` — environment-based settings, validated at startup
- `backend/core/logging_setup.py` — console + rotating file logging
- `backend/core/event_bus.py` — async pub/sub event bus
- `backend/main.py` — entry point proving the above work together
- `backend/tests/test_event_bus.py` — unit tests for the event bus
- `config/.env.example` — template for required environment variables
- `docs/architecture.md`, `docs/roadmap.md` — living documentation

## Next up — Module 2: AI Brain

Goal: a working text conversation with Claude, end to end, callable
from `backend/main.py`, with the reasoning engine behind an interface
so a local model can later be substituted without changing any code
that *calls* the AI module.
