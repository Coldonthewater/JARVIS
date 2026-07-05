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
