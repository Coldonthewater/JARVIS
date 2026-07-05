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
| `ai_response_ready` | `ai.engine` | `{provider, model, category, routed_local, escalated_for_confidence}` | `main.py` (logs it) — future: gateway will use this to stream responses to clients |





- **Module 2 (AI brain)**: `backend/ai/` — a reasoning engine
  abstraction so Claude (cloud) and local models are interchangeable
  behind one interface.
- **Module 3 (Gateway)**: `backend/gateway/` — REST + WebSocket API,
  client registry, auth. This is what every future client (desktop,
  mobile, wall display, AR) will connect to.
- **Module 4 (Memory)**: `backend/memory/` — local database for
  conversation history, preferences, devices, automation rules.
- **Module 5 (Integrations)**: `backend/integrations/` — plugin
  pattern, one folder per service, all implementing a shared interface.
- **Module 6 (Voice)**: `backend/voice/` — wake word, STT, TTS.
- **Module 7+ (Clients)**: `clients/desktop/`, then others.

See `roadmap.md` for the full phased plan.
