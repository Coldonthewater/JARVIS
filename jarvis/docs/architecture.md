# Jarvis — Architecture

_Last updated: Module 1 (Core Backend)_

## Guiding Principle

The backend is a standalone "brain" with no knowledge of any specific
client (desktop, mobile, wall display, AR glasses). Clients connect to
a transport-agnostic **gateway** and never talk to internal modules
directly. This is what lets us build one backend and many front ends.

```
┌─────────────────────────────────────────────────────────┐
│                        CLIENTS                            │
│   Desktop  │  Mobile  │  Wall Display  │  AR Glasses       │
└───────────────────────┬───────────────────────────────────┘
                         │  REST + WebSocket (JSON)
┌────────────────────────▼──────────────────────────────────┐
│                      GATEWAY                               │
│   - REST API (request/response actions)                    │
│   - WebSocket (streaming chat, live events)                │
│   - Client registry & capability negotiation                │
│   - Auth (token-based, resolves to one user identity)       │
└────────────────────────┬──────────────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────────────┐
│                    EVENT BUS (core)                         │
│   Modules publish/subscribe to events without knowing       │
│   about each other. Decouples everything below.             │
└──┬─────────┬──────────┬───────────┬───────────┬────────────┘
   │         │          │           │           │
┌──▼───┐ ┌───▼────┐ ┌───▼─────┐ ┌──▼──────┐ ┌───▼─────────┐
│  AI  │ │ Memory │ │  Voice  │ │Integra- │ │   (future   │
│      │ │        │ │         │ │ tions   │ │   modules)  │
└──────┘ └────────┘ └─────────┘ └─────────┘ └─────────────┘
```

## Module 1: Core Backend (current state)

| File | Responsibility |
|---|---|
| `backend/core/config.py` | Loads and validates all configuration from environment variables / `.env`. Single source of truth — every module reads config from here, never `os.environ` directly. |
| `backend/core/logging_setup.py` | Configures consistent logging (console + rotating file) for every module via `get_logger(__name__)`. |
| `backend/core/event_bus.py` | In-process async publish/subscribe bus. Decouples modules so they can be added/removed without rewriting others. |
| `backend/main.py` | Entry point. Currently just proves the foundation boots and the event bus delivers events end-to-end. Will grow to start the gateway, AI, memory, integrations, and voice in later modules. |

### Why an event bus before anything else?

Every module added from here forward (AI, memory, voice, integrations,
gateway) will communicate by publishing and subscribing to events
rather than importing each other directly. Establishing this pattern
in Module 1 — even before there's anything interesting to put events
about — means we never have to retrofit it later under deadline
pressure.

### Key events (grows as modules are added)

| Event name | Published by | Payload | Subscribed by |
|---|---|---|---|
| `system_startup` | `main.py` | `{message: str}` | (example only, for now) |

This table will be kept current as each module introduces new events.

## Module 2: AI Brain (current state)

Hybrid routing across local and cloud providers, all behind one interface.
Routing is **category-based**, not a fuzzy complexity score — each
request is classified into a named category, and each category maps
to a fixed tier (local or cloud).

```
User message
     │
     ▼
Conversation (history)
     │
     ▼
Router.classify() ── category ──► LOCAL categories:
     │                             everyday_conversation, app_control,
     │                             smart_home, weather,
     │                             memory_preference, automation
     │                             → settings.ai_local_provider (default: ollama)
     │
     └──────────────────────────► CLOUD categories:
                                   code, planning, research,
                                   document_summary
                                   → settings.ai_cloud_provider (default: openai)

Local response uncertain? (router.response_seems_uncertain)
     │
     ▼
Escalate to settings.ai_cloud_provider

Provider unreachable/unconfigured at any point?
     │
     ▼
Fall back to settings.ai_fallback_provider
```

| File | Responsibility |
|---|---|
| `backend/ai/base.py` | The `AIProvider` interface (Protocol) every provider adapter must implement. This is what makes "any provider" possible. |
| `backend/ai/providers/*.py` | One file per provider (Ollama, OpenAI, Gemini, Anthropic). Each isolates that provider's SDK/API quirks — nothing outside this file needs to know they exist. |
| `backend/ai/router.py` | Classifies each message into a `Category` (everyday_conversation, app_control, smart_home, weather, memory_preference, automation, code, planning, research, document_summary) via keyword matching, exposes `is_local_category()` to map a category to its tier, and `response_seems_uncertain()` for confidence-based escalation. |
| `backend/ai/conversation.py` | Holds message history for one conversation session, independent of which provider handles any given turn. In-memory for now — moves to the database in Module 4. |
| `backend/ai/engine.py` | Public entry point (`ai_engine.respond(...)`). Orchestrates classification, provider calls, confidence-based escalation, and availability fallback. Every other module (voice, gateway) will call this and nothing else. |

### Why local-first

Local (Ollama) handles everyday conversation, app control, smart home
commands, weather, remembering preferences, and automations — these
are latency-sensitive, low-stakes, and should keep working with no
internet connection. Cloud is reserved for requests that actively earn
it: complex code, long-term planning, research, and summarizing large
documents — plus any local answer that reads as unconfident, which
gets automatically re-answered by the cloud provider.

### Adding a new provider

1. Create `backend/ai/providers/newprovider_provider.py` implementing the `AIProvider` interface (`generate()`, `is_available()`).
2. Register it in `AIEngine._providers` in `engine.py`.
3. Point any of `AI_LOCAL_PROVIDER` / `AI_CLOUD_PROVIDER` / `AI_FALLBACK_PROVIDER` at it via config.

No other file changes needed — this is the payoff of the interface-based design.

### Adding or tuning a category

Add a case to `Category`, add it to `LOCAL_CATEGORIES` or `CLOUD_CATEGORIES`, and add its keyword signals to `_CATEGORY_KEYWORDS` — all in `router.py`. No other file changes needed.

### New events

| Event name | Published by | Payload | Subscribed by |
|---|---|---|---|
| `ai_response_ready` | `ai.engine` | `{provider, model, category, routed_local, escalated_for_confidence}` | `main.py` (logs it), gateway (returns it to the client that asked) |

## Module 3: Gateway (current state)

The single API surface every client connects through — REST for
request/response, WebSocket for real-time.

```
Client (desktop, mobile, wall display, AR glasses)
     │
     │  Authorization: Bearer <GATEWAY_AUTH_TOKEN>
     ▼
┌─────────────────────────────────────────────┐
│                  Gateway                      │
│  REST: /health  /clients/register  /chat      │
│  WebSocket: /ws/chat                          │
│  Auth: shared bearer token (auth.py)          │
│  Client registry: capabilities, not client type│
└───────────────────┬───────────────────────────┘
                     │
                     ▼
              ai_engine.respond()
```

| File | Responsibility |
|---|---|
| `backend/gateway/auth.py` | Verifies the bearer token every request must carry. One shared token for now — see "Auth model" below. |
| `backend/gateway/client_registry.py` | Tracks connected clients by declared **capabilities** (has_microphone, has_display, etc.), not by hardcoded client type — this is what lets a new client type connect with zero backend changes. |
| `backend/gateway/rest/app.py` | FastAPI application factory. |
| `backend/gateway/rest/routes.py` | `/health` (unauthenticated), `/clients/register`, `/chat`. |
| `backend/gateway/rest/schemas.py` | Request/response models — also the source of the auto-generated OpenAPI docs at `/docs`. |
| `backend/gateway/ws/routes.py` | `/ws/chat` — same underlying `ai_engine.respond()` call, over a persistent connection. Foundation for future streaming/push events. |
| `backend/gateway/ws/connection_manager.py` | Tracks live WebSocket objects, separate from the client registry (a client can be registered without holding an open socket). |
| `backend/setup.py` | First-run setup wizard — creates `config/.env` interactively (generates the gateway token, asks about providers and network access) so no config file needs hand-editing to get started. Runs automatically on first `python -m backend.main`; re-runnable anytime via `python -m backend.setup`. |

### Auth model

A single long-lived bearer token (`GATEWAY_AUTH_TOKEN`), not OAuth.
OAuth is for Module 5, where Jarvis authenticates *to* external
services (Google, Microsoft) on your behalf — a different direction
entirely. This token is how *your own devices* prove to Jarvis they're
allowed to connect. Simple by design: revoking a device today means
rotating the shared token (all devices need updating); a future
upgrade path is per-device tokens if that granularity is ever needed —
the `verify_token()` interface won't need to change for callers.

### Remote access: reaching the gateway from other devices

The gateway binds to `127.0.0.1` (localhost-only) by default — safe,
but only reachable from the same machine. Since Jarvis's home base is
the Windows PC and you want to reach it from a MacBook, phone, etc.,
you have two options:

1. **LAN only**: set `GATEWAY_HOST=0.0.0.0` in `.env` and connect
   using the Windows PC's local IP (e.g. `192.168.1.x:8000`). Only
   works when both devices are on the same WiFi/network, and exposes
   the port to anything else on that network too.
2. **Tailscale (recommended)**: install Tailscale on the Windows PC
   and on each client device. It creates a private, encrypted network
   between just your own devices, with each getting a stable Tailscale
   IP — reachable from anywhere (not just the same WiFi), without
   exposing the gateway to the open internet. `GATEWAY_HOST=0.0.0.0`
   is still needed so the gateway accepts connections beyond
   localhost, but only devices on your Tailscale network can actually
   reach it.

Either way, `GATEWAY_AUTH_TOKEN` must be set before binding beyond
localhost — the gateway logs a warning at startup if it isn't.

### New events

(No new events published in Module 3 — the gateway consumes
`ai_response_ready`'s data via the `EngineResult` returned directly
from `ai_engine.respond()`, rather than subscribing to the event bus.
The event bus publish still happens in `engine.py` for any other
module — e.g. future logging/analytics — that wants to observe AI
activity without being in the direct request path.)

## Coming in later modules

- **Module 4 (Memory)**: `backend/memory/` — local database for
  conversation history, preferences, devices, automation rules.
- **Module 5 (Integrations)**: `backend/integrations/` — plugin
  pattern, one folder per service, all implementing a shared interface.
- **Module 6 (Voice)**: `backend/voice/` — wake word, STT, TTS.
- **Module 7+ (Clients)**: `clients/desktop/`, then others.

See `roadmap.md` for the full phased plan.
