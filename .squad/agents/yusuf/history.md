# History

## Core Context
Project: A Python backend and TypeScript frontend for a 2-hour hackathon, aiming for a high-quality MVP. Awaiting the product challenge. User: Drew Robbins.
Tech: Python, TypeScript, Aspire toolkit, OpenTelemetry, Azure App Insights, Azure CI/CD.

## Learnings
- Built 4 endpoints in main.py: GET /api/scenarios, POST /api/session, POST /api/transcript, POST /api/coaching
- Used httpx.AsyncClient for the Vocal Bridge token call (async-friendly, follows helloworld server.py pattern)
- Coaching endpoint uses OpenAI gpt-4o with JSON response format; falls back to mock if OPENAI_API_KEY not set
- Scenarios endpoint filters to trainee-visible fields only (id, title, difficulty, description) — persona/strategy never exposed
- Transcripts stored in-memory dict keyed by uuid4, sufficient for hackathon MVP
- Added httpx and openai to requirements.txt
- Created setup_agents.py following helloworld pattern — creates both sim + coaching agents via vb CLI
- POST /api/session now reconfigures VB agent dynamically per scenario using `vb` CLI: sets prompt (simulation_prompt.md + employee manual + scenario context), greeting (opening_line from scenario), model settings (voice_id, voice_style per scenario), and client actions
- Added POST /api/coaching-session endpoint for coaching mode: reconfigures VB with coaching prompt, coach voice (VR6AewLTigWG4xSOukaG/professional), coaching client actions, and a warm coaching greeting
- scenarios.json now includes voice_id and voice_style per scenario (ElevenLabs voice IDs mapped to personas)
- VB CLI helper pattern: _find_vb() via shutil.which, _run_vb() with subprocess.run(capture_output=True), temp files via tempfile.NamedTemporaryFile(delete=False) with try/finally cleanup
- Token acquisition extracted into shared _get_vb_token() helper used by both session endpoints
- Key VB CLI commands: `vb prompt set -f FILE`, `vb config set --greeting TEXT`, `vb config set --model-settings-file FILE`, `vb config set --client-actions-file FILE`
- Added comprehensive OpenTelemetry tracing alongside existing OTel logging in _setup_otel(): TracerProvider + BatchSpanProcessor + OTLPSpanExporter, mirroring the same grpc/http protocol detection pattern used for logs
- Created module-level `tracer = trace.get_tracer("voicecoach")` after _setup_otel() for use across all spans
- Auto-instrumented FastAPI routes via `FastAPIInstrumentor.instrument_app(app)` and outbound httpx calls via `HTTPXClientInstrumentor().instrument()`
- Added custom spans with `tracer.start_as_current_span()` to: ensure_agent, setup_agents, create_session, create_coaching_session, vb_token_request, store_transcript, get_coaching, build_feedback_messages, openai_chat_completion
- Pattern for error handling in spans: `span.set_status(StatusCode.ERROR, str(exc))` + `span.record_exception(exc)` + re-raise
- Added opentelemetry-instrumentation-fastapi and opentelemetry-instrumentation-httpx to requirements.txt
- Added POST /api/telemetry (batch) and POST /api/telemetry/event (single) endpoints to main.py for frontend-reported conversation events (transcript turns, client actions, session lifecycle). These create OTel spans under the existing voicecoach tracer so LiveKit room events become visible in Aspire traces.
- TelemetryEvent schema: session_id, event_type (validated against allowlist), action, direction, payload, timestamp
- Span naming convention: "{event_type}:{action}" (e.g. "client_action:session_context", "transcript_turn:agent")
- Batch endpoint groups events under a "telemetry_batch" parent span; single endpoint uses "telemetry_single"

📌 Team update (2026-03-26): Telemetry architecture redesigned — backend needs: agent.id on vb_token_request span, scenario.id on create_coaching_session span, span around VB CLI calls, session.phase attribute on all backend spans, session.id propagated consistently. See docs/telemetry-architecture.md §6. — decided by Arthur (synthesizing Yusuf, Eames, Browning)
- Transcript text truncated to 1024 chars in span attributes to avoid OTel payload bloat
- Implemented session-scoped tracing: all telemetry events and API calls for a session+phase share one trace_id. Uses `_session_contexts` dict mapping `session_id:phase` → `SpanContext`, with `NonRecordingSpan` as synthetic parent. Three phases: simulation, coaching, feedback.
- `_get_or_create_session_context(trace_key, root_name)` creates one root span per trace_key and reuses its trace_id for all subsequent spans. Returns an OTel Context for `start_as_current_span(name, context=ctx)`.
- Phase inference: `_infer_phase()` checks `event.phase` first, then action name against `_SIMULATION_ACTIONS`/`_COACHING_ACTIONS` sets, defaults to "simulation".
- Added `trace_session_id` field to SessionRequest, CoachingSessionRequest, CoachingRequest, TranscriptRequest for opt-in session trace grouping. When None, spans create standalone traces (backward compatible).
- Removed wrapping parent spans from telemetry batch/single endpoints — each event now self-parents to its session trace via `_record_telemetry_event`.
- API endpoints (session, coaching-session, transcript, coaching) now accept `trace_session_id` and join the appropriate phase trace. VB token calls and OpenAI calls automatically nest under the parent span context.
- Removed client telemetry relay from backend (TELEMETRY_DEBUG flag, TelemetryEvent/TelemetryBatch models, VALID_EVENT_TYPES, _infer_phase, _record_telemetry_event, /api/telemetry endpoints). Frontend now owns its own OTel spans via Node.js SDK. Backend OTel setup (_setup_otel, tracer, TracerProvider) and session-scoped tracing (_session_contexts, _get_or_create_session_context) remain intact for business endpoint traces.
- Removed `api/telemetry` from FastAPIInstrumentor excluded_urls since the route no longer exists.
