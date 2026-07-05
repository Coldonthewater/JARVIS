# Jarvis

A real-life, modular AI assistant inspired by Iron Man's JARVIS.

This is a long-term, production-quality project — see `docs/` for
architecture, roadmap, and coding standards.

## Current Status

**Module 3: Gateway** — complete. Jarvis now runs as a real API
server (REST + WebSocket) instead of only a terminal loop, so any
client — including other devices on your network — can talk to it.
No persistent memory, voice, or dashboard UI yet — those come in later
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

4. **Run it:**
   ```
   python -m backend.main
   ```
   No config file to create by hand — the **first time** you run this,
   a setup wizard walks you through it right there in the terminal:
   generates a secure gateway token automatically, asks whether to use
   a local model (Ollama) and/or lets you paste a cloud API key, and
   asks about network access. It writes `config/.env` for you.

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
   Tests use fake providers and a test HTTP client — no API keys,
   Ollama, or a real network port needed.

## Accessing Jarvis from another device (MacBook, phone, etc.)

By default the gateway only listens on `127.0.0.1` (this machine
only). The setup wizard asks about this on first run — if you said no
then, or want to change it later, re-run `python -m backend.setup`, or
edit `config/.env` directly:

1. Set `GATEWAY_HOST=0.0.0.0` (and make sure `GATEWAY_AUTH_TOKEN` is
   set — the gateway will warn at startup if it isn't).
2. **Recommended**: install [Tailscale](https://tailscale.com) on this
   Windows PC and on your other devices. It creates a private,
   encrypted network between just your own devices, reachable from
   anywhere — not just the same WiFi — without exposing the gateway to
   the open internet. Connect using the Windows PC's Tailscale IP.
3. Alternative (same-WiFi only): connect using this PC's local network
   IP instead (find it with `ipconfig` on Windows, look for "IPv4
   Address").

Every request from another device needs the `Authorization: Bearer
<token>` header set to your `GATEWAY_AUTH_TOKEN` (shown once during
setup — also viewable anytime by opening `config/.env`).

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
│   ├── memory/       # Local database, preferences, history (Module 4)
│   ├── integrations/ # Plugin-based external service connectors (Module 5)
│   ├── voice/        # Wake word, STT, TTS (Module 6)
│   ├── tests/        # Unit tests, mirrors backend/ structure
│   ├── main.py       # Entry point — starts the gateway (or --chat mode)
│   └── setup.py      # First-run setup wizard — creates config/.env for you
├── clients/          # Front ends (desktop, mobile, etc.) — Module 7+
├── config/           # .env file lives here (never committed)
├── docs/             # Architecture, roadmap, standards — read these first
└── requirements.txt
```

## Documentation

Start with `docs/architecture.md` for the system design and
`docs/roadmap.md` for what's built vs. planned.
