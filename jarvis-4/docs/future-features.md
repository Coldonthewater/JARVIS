# Jarvis — Future Features (Parking Lot)

Ideas that come up during development but aren't part of the current
module's scope. Captured here so they aren't lost, and so they don't
derail current work.

- **Smarter request routing**: the router now uses explicit categories
  (conversation, app control, smart home, weather, memory, automation
  -> local; code, planning, research, summarization -> cloud) plus
  confidence-based escalation. A future version could use a tiny local
  model to classify intent instead of keyword matching, for better
  accuracy as new phrasing patterns show up in real usage.
- **Per-task provider selection**: route not just by simple/complex,
  but by task type (e.g. always use a specific provider for code,
  another for creative writing) once there's enough usage data to
  justify it.
- **Cross-device / remote access**: the gateway (Module 3) is built
  with this in mind — client registry, capability negotiation, bearer
  auth all already exist — but it's deliberately locked to
  localhost-only for now (`gateway_host` is force-corrected in
  `backend/core/config.py`). When revisited: allow `GATEWAY_HOST=0.0.0.0`
  and recommend Tailscale for reaching the gateway from a MacBook,
  phone, wall display, etc. without exposing it to the open internet.
  Natural time to revisit: when building the first non-terminal client
  (Module 7, desktop dashboard) or sooner if needed.
- **Database migrations (Alembic)**: Module 4 uses
  `Base.metadata.create_all()` to create tables, which can't safely
  evolve an existing column once real data exists. Fine while the
  schema is still moving quickly; revisit once it stabilizes so future
  changes don't risk losing conversation history or preferences.
- **Preference auto-extraction**: right now `PreferenceRepository` is
  pure storage — something else (a future module, or smarter AI engine
  logic) needs to decide *when* a conversation implies a preference
  worth saving (e.g. "remember that I like jazz" -> actually calling
  `preference_repository.set(...)`). Not built yet; the router's
  `memory_preference` category currently just routes such messages
  locally without acting on them.
- **REST endpoints for rooms/devices/automations/notes**: repositories
  and tests exist (Module 4) but no API surface yet — add when Module 5
  (integrations) or the dashboard actually needs to read/write them.
