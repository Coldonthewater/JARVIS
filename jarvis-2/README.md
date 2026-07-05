# Jarvis

A real-life, modular AI assistant inspired by Iron Man's JARVIS.

This is a long-term, production-quality project — see `docs/` for
architecture, roadmap, and coding standards.

## Current Status

**Module 1: Core Backend** — complete. Foundation only (config,
logging, event bus). No AI, voice, or UI yet — those come in later
modules per `docs/roadmap.md`.

## Setup

1. **Install Python 3.12+**

2. **Create a virtual environment** (keeps dependencies isolated from
   the rest of your system):
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS/Linux
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Set up your environment file:**
   ```
   copy config\.env.example config\.env     # Windows
   cp config/.env.example config/.env        # macOS/Linux
   ```
   Leave values blank for now — Module 1 doesn't require any.

5. **Run it:**
   ```
   python -m backend.main
   ```
   You should see log lines confirming the app started, the gateway
   port it would use, and a demo event being published/handled. This
   proves config, logging, and the event bus are all working together.

6. **Run the tests:**
   ```
   pytest
   ```

## Project Structure

```
jarvis/
├── backend/          # The "brain" — all server-side logic
│   ├── core/         # Config, logging, event bus (foundation)
│   ├── ai/           # Reasoning engine (Module 2)
│   ├── gateway/      # REST + WebSocket API for all clients (Module 3)
│   ├── memory/       # Local database, preferences, history (Module 4)
│   ├── integrations/ # Plugin-based external service connectors (Module 5)
│   ├── voice/        # Wake word, STT, TTS (Module 6)
│   └── tests/        # Unit tests, mirrors backend/ structure
├── clients/          # Front ends (desktop, mobile, etc.) — Module 7+
├── config/           # .env file lives here (never committed)
├── docs/             # Architecture, roadmap, standards — read these first
└── requirements.txt
```

## Documentation

Start with `docs/architecture.md` for the system design and
`docs/roadmap.md` for what's built vs. planned.
