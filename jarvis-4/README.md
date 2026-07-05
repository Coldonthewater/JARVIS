# Jarvis

A real-life, modular AI assistant inspired by Iron Man's JARVIS.

This is a long-term, production-quality project — see `docs/` for
architecture, roadmap, and coding standards.

## Current Status

**Module 4: Memory** — complete. Conversations now persist to a local
SQLite database and survive a restart, along with preferences, rooms,
devices, automations, and notes. Still localhost-only by design (see
`docs/future-features.md`), and no voice or dashboard UI yet — those
come in later modules per `docs/roadmap.md`.

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

4. **Run it:**
   ```
   python -m backend.main
   ```
   No config file to create by hand — the **first time** you run this,
   a setup wizard walks you through it right there in the terminal:
   generates a secure gateway token automatically, and asks whether to
   use a local model (Ollama) and/or lets you paste a cloud API key.
   It writes `config/.env` for you.

   After that first run, Jarvis starts normally with no prompts. Want
   to change your setup later (add a key, switch providers)? Re-run
   the wizard anytime:
   ```
   python -m backend.setup
   ```
   (Or just edit `config/.env` directly if you prefer — the wizard is
   a convenience, not a requirement.)

   Once running, the gateway server listens at `http://127.0.0.1:8000`.
   Open `http://127.0.0.1:8000/docs` in a browser for interactive API
   docs (click "Authorize" and paste your token to try `/chat` from
   there).

   Prefer a plain terminal chat loop instead of the API server?
   ```
   python -m backend.main --chat
   ```

5. **Run the tests:**
   ```
   pytest
   ```
   Tests use fake providers, a test HTTP client, and an isolated
   in-memory database — no API keys, Ollama, a real network port, or
   your actual `data/jarvis.db` are touched.

## About remote access

Jarvis currently runs **localhost-only** — cross-device access (from a
MacBook, phone, etc.) is deferred for now by design. The gateway is
still built to support it later (see `docs/architecture.md` and
`docs/future-features.md`), but for the moment everything talks to
Jarvis from the same machine it's running on.

## Project Structure

```
jarvis/
├── backend/          # The "brain" — all server-side logic
│   ├── core/         # Config, logging, event bus (foundation)
│   ├── ai/           # Hybrid local/cloud reasoning engine
│   │   └── providers/  # One adapter per AI provider
│   ├── gateway/      # REST + WebSocket API for all clients
│   │   ├── rest/       # FastAPI app, routes, schemas
│   │   └── ws/         # WebSocket chat + connection manager
│   ├── memory/       # SQLite database, repositories (conversations, preferences, rooms, devices, automations, notes)
│   │   └── repositories/  # The only files that touch the ORM directly
│   ├── integrations/ # Plugin-based external service connectors (Module 5)
│   ├── voice/        # Wake word, STT, TTS (Module 6)
│   ├── tests/        # Unit tests, mirrors backend/ structure
│   ├── main.py       # Entry point — starts the gateway (or --chat mode)
│   └── setup.py      # First-run setup wizard — creates config/.env for you
├── clients/          # Front ends (desktop, mobile, etc.) — Module 7+
├── config/           # .env file lives here (never committed)
├── data/             # jarvis.db (SQLite) — created automatically, never committed
├── docs/             # Architecture, roadmap, standards — read these first
└── requirements.txt
```

## Documentation

Start with `docs/architecture.md` for the system design and
`docs/roadmap.md` for what's built vs. planned.
