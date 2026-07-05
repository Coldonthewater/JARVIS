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

## Coming in later modules

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
