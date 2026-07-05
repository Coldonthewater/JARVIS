# Jarvis — Coding Standards

## General

- **Python 3.12+**, type hints on every function signature.
- Every module/class/function gets a docstring explaining **why** it
  exists, not just what it does — the "why" is what keeps a project
  maintainable after months away from it.
- No bare `except:` — always catch specific exceptions.
- No `print()` for anything other than throwaway local debugging —
  use `get_logger(__name__)` from `backend.core.logging_setup`.
- No hardcoded secrets, ever. All config comes from
  `backend.core.config.settings`.

## Module structure

- One responsibility per file. If a file is doing two unrelated
  things, split it.
- Cross-module communication goes through the **event bus**
  (`backend.core.event_bus`) wherever possible, not direct imports
  between sibling modules (e.g., `voice/` should not import from
  `integrations/` directly).
- New integrations implement the shared `Integration` interface
  (defined in Module 5) — see `docs/integrations.md`.

## Testing

- Every module gets a matching file under `backend/tests/`, e.g.
  `backend/core/event_bus.py` → `backend/tests/test_event_bus.py`.
- Use `pytest` + `pytest-asyncio` for async code.
- Aim to test behavior (what the function guarantees), not
  implementation details.

## Naming

- `snake_case` for files, functions, variables.
- `PascalCase` for classes.
- Event names: lowercase, snake_case, past tense (e.g. `user_spoke`,
  `integration_connected`).

## Documentation

- `docs/architecture.md` is updated at the end of every module with
  what was added and why.
- `docs/roadmap.md` status column is updated as modules complete.
