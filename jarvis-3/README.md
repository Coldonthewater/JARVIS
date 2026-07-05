# Jarvis

A real-life, modular AI assistant inspired by Iron Man's JARVIS.

This is a long-term, production-quality project — see `docs/` for
architecture, roadmap, and coding standards.

## Current Status

**Module 2: AI Brain** — complete. You can now have a real terminal
conversation with Jarvis, hybrid-routed between a local model (Ollama)
and cloud providers (OpenAI, Gemini, or Anthropic). No memory, voice,
or UI yet — those come in later modules per `docs/roadmap.md`.

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
   You need **at least one** AI provider configured for the chat loop
   to work:
   - **Easiest / free**: install [Ollama](https://ollama.com), run
     `ollama pull llama3.1`, leave the rest of the AI settings at
     their defaults.
   - **Cloud**: get a developer API key (billed by usage, not your
     ChatGPT Plus/Gemini Advanced login) from
     [platform.openai.com](https://platform.openai.com/api-keys),
     [Google AI Studio](https://aistudio.google.com/apikey), or
     [console.anthropic.com](https://console.anthropic.com), and set
     it in `config/.env`.

5. **Run it:**
   ```
   python -m backend.main
   ```
   This starts a terminal chat loop — type a message and Jarvis will
   respond, showing which provider handled it (e.g. `Jarvis
   (ollama/llama3.1): ...`). Type `quit` to exit.

6. **Run the tests:**
   ```
   pytest
   ```
   Tests use fake providers and don't require any API keys or Ollama
   to be running.

## Project Structure

```
jarvis/
├── backend/          # The "brain" — all server-side logic
│   ├── core/         # Config, logging, event bus (foundation)
│   ├── ai/           # Hybrid local/cloud reasoning engine
│   │   └── providers/  # One adapter per AI provider
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
