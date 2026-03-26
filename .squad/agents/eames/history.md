# History

## Core Context
Project: A Python backend and TypeScript frontend for a 2-hour hackathon, aiming for a high-quality MVP. Awaiting the product challenge. User: Drew Robbins.
Tech: Python, TypeScript, Aspire toolkit, OpenTelemetry, Azure App Insights, Azure CI/CD.

## Learnings
- Built VoiceCoach frontend as single-page app with 3 screens (picker → simulation → coaching) using plain HTML + CSS + vanilla JS — no frameworks. Matches the helloworld web_embed pattern.
- LiveKit connection pattern: load UMD from CDN, handle `RoomEvent.DataReceived` for `send_transcript` and `end_simulation` client actions, send `session_context` via `publishData`.
- API proxy pattern: Express middleware at `/api` path forwards to backend via Node https module with `rejectUnauthorized: false` for dev certs. Backend URL from Aspire env var `services__backend__https__0`.
- Coaching results API returns: `overall_score`, `scores[]` with category/score/max_score/manual_section/summary, `improvement_areas[]`, `coaching_dialogue`.
- Dark UI theme: #0f1023 bg, #6c63ff accent, green/amber/red for score tiers (≥8/5-7/<5).
- Coaching voice call: added second LiveKit connection (`coachingRoom`) for `POST /api/coaching-session` endpoint. Uses separate transcript box and visualizer within the coaching results screen. No `session_context` data channel needed — backend bakes context into the coaching agent prompt.
- `appendTranscript` now accepts an optional `targetBox` param to route lines to either the simulation or coaching transcript. Agent label is "Customer" for simulation, "Coach" for coaching.
- Coaching-specific client actions: `send_evaluation` (displays evaluation text in coaching transcript), `end_conversation` (disconnects coaching room).
- Flow: scenario picker → simulation voice call → scores + coaching results → optional coaching voice call → retry.
- Telemetry instrumentation: added fire-and-forget `reportTelemetry()` helper that POSTs to `/api/telemetry/event`. Reports session_lifecycle (start/end/connect/disconnect), client_action (session_context, feedback_data, transcript_data, end_simulation, end_conversation), and transcript_turn events. `sessionId` state variable initialized at simulation start (`scenario.id + "-" + Date.now()`), updated to backend-assigned session_id from POST /api/transcript response when available.
- Session-scoped tracing: all `reportTelemetry` calls now include a `phase` field ("simulation" or "coaching") so the backend can group spans under session-scoped traces in Aspire. All four API bodies (POST /api/session, /api/transcript, /api/coaching, /api/coaching-session) pass `trace_session_id: sessionId` so backend joins events to the same trace.
- Telemetry payload summaries: `reportTelemetry` for `feedback_data` now includes `overall_score`, `scores_count`, `improvement_areas_count`, `has_coaching_dialogue`. For `transcript_data`, includes `transcript_count`. Backend's `_record_telemetry_event` already captures `event.payload` fields as span attributes on `client_action` spans — these summaries make the data inspectable in Aspire traces without shipping full payloads.
- Client action delivery ordering: Added 100ms `setTimeout` delay between `publishData` for `feedback_data` and `transcript_data` in the coaching room `RoomEvent.Connected` handler. LiveKit `publishData` doesn't guarantee ordering; the coaching prompt expects feedback first, transcript second. Code location: `src/frontend/public/index.html` around line 1038-1072.
- OpenTelemetry migration: Moved client telemetry from custom REST endpoint (`/api/telemetry/event` → Python backend) to native OTel on the Node.js frontend server (`/telemetry` → `server.js`). Uses `@opentelemetry/sdk-node` + `@opentelemetry/exporter-trace-otlp-grpc` to export spans via gRPC to Aspire's OTLP collector. NodeSDK reads `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME` etc. from env vars injected by Aspire automatically.
- Session-scoped trace context ported to Node.js: `sessionContexts` Map keyed by `{session_id}:{phase}` creates root spans per phase, then attaches all subsequent events as children. Same grouping pattern as the Python backend had.
- `/telemetry` endpoint is defined BEFORE the `/api` proxy middleware in server.js — this prevents it from being proxied to the backend.
- `express.json()` middleware added before static files to parse JSON bodies from telemetry POSTs.
- `reportTelemetry()` in index.html now POSTs to `/telemetry` (not `/api/telemetry/event`). Event payload format is unchanged.

📌 Team update (2026-03-26): Telemetry architecture redesigned — rewrite otel-browser.js with new startPhase()/PhaseContext API, replace all browser OTel logs with span events, remove LoggerProvider/OTLPLogExporter, add room_connect span, make conversation a long-lived span with transcript turn events. See docs/telemetry-architecture.md. — decided by Arthur (synthesizing Yusuf, Eames, Browning)
- Rewrote `src/frontend/otel-browser.js` to implement the Section 4 browser telemetry API from `docs/telemetry-architecture.md`. New public API: `window.__otel = { ready, startPhase, tracedFetch }`. Removed `createSpan`, `emitLog`, `getOrCreateSessionContext`, `endSessionContext`.
- `startPhase(sessionId, phase, attrs)` returns a PhaseContext: `{ rootSpan, ctx, createChildSpan, addEvent, end }`. Child spans from `createChildSpan` return `{ span, addEvent, setAttribute, end }`.
- Critical bug fix: log records now properly correlated to spans via `trace.setSpan(context.active(), targetSpan)` passed as `context:` to `logger.emit()`. The old `emitLog` was passing a reconstructed span context that didn't carry the real span reference, so log records were invisible in Aspire.
- `addEvent` on both PhaseContext (root) and child spans emits log records via `logger.emit()` with `"event.name"` attribute set — follows OTel deprecation of `Span.AddEvent`.
- `tracedFetch` now takes `(url, options, phaseContext)` instead of `(url, options, sessionId, phase)`. Falls back to `context.active()` if no phaseContext provided.
- Kept LoggerProvider + OTLPLogExporter in the bundle — these are core to the log-record-as-event approach.
