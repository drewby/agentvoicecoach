# VoiceCoach Telemetry Architecture

## 1. Current State

> **Status: Implemented.** The architecture described in this document is live and producing traces in the Aspire dashboard. The screenshot below shows a real simulation trace.

![Aspire simulation trace](Aspire%20screenshot.png)

The frontend telemetry (`otel-browser.js` + `index.html`) implements the phase-based API described in Section 4. Each session phase — simulation, feedback, coaching — creates a single root span with a structured hierarchy of child spans reflecting real work: `fetch /api/session` → `room_connect` → `send_session_context` → `conversation` → `fetch /api/transcript` → `cleanup`. The `conversation` span is long-lived (30s–5min) and carries `transcript_turn` log records correlated via OTel context — each turn is visible in the Aspire structured logs view linked to its parent trace.

The browser OTel stack uses:
- `WebTracerProvider` + `BatchSpanProcessor` → OTLP HTTP → Aspire `/v1/traces`
- `LoggerProvider` with `processors` constructor option + `SimpleLogRecordProcessor` → OTLP HTTP → Aspire `/v1/logs`
- Both exporters send directly to the Aspire dashboard endpoint (CORS handled by Aspire)

The backend (`main.py`) has manual spans on all business operations (`create_session`, `create_coaching_session`, `store_transcript`, `build_feedback_messages`, `get_coaching`, `openai_chat_completion`, `vb_token_request`, `ensure_agent`, `setup_agents`), plus auto-instrumented FastAPI routes and HTTPX calls. Backend spans carry `agent.id`, `scenario.id`, `session.phase`, and `session.id` attributes. VB CLI calls are wrapped in `vb_cli` spans with `vb.command` attributes.

The trace viewer shows a clean waterfall: browser spans (red) interleave with backend spans (amber), giving full visibility from button click through API call through Vocal Bridge token acquisition and back.

---

## 2. Design Principles

1. **Spans wrap real work.** A span starts when meaningful work begins and ends when that work completes. If the "work" is a 1ms `publishData()` call, it's not a span — it's a span event on a parent span.

2. **Use log records for point-in-time events, correlated to traces via context.** OTel is [deprecating `Span.AddEvent`](https://opentelemetry.io/blog/2026/deprecating-span-events/) in favor of log-based events emitted via the Logs API and associated with the active span through context. We follow this direction: transcript turns, lifecycle transitions, and client action annotations are log records with `event.name`, not span events. They carry trace/span context automatically and appear in the Aspire log view linked to their parent trace.

3. **One trace per session phase, structured in work blocks.** Each phase (simulation, feedback, coaching) gets one trace with a hierarchy of spans reflecting the actual timeline: setup → conversation → cleanup. Not one span per micro-operation. If the user restarts the coaching session, that is also a new trace. 

4. **Inputs and outputs on client actions are log record attributes.** When data is sent to or received from an agent, the payload content appears as attributes on a log record (with `event.name` set) so developers can debug without guessing.

5. **Consistent attributes everywhere.** Same attribute names in frontend and backend. Same `session.id`, `scenario.id`, `session.phase` across all spans and events.

---

## 3. Trace Structure

### 3.1 Simulation Phase

```
simulation (root span)
│   attributes: session.id, scenario.id, scenario.title, scenario.difficulty
│
├── setup
│   │   attributes: session.id
│   │
│   ├── fetch POST /api/session
│   │       attributes: http.method, http.url, http.status_code
│   │
│   ├── room_connect
│   │       attributes: livekit.url
│   │       starts: getUserMedia() called
│   │       ends: room Connected event fires
│   │       log events (correlated via span context):
│   │         - media_acquired (when getUserMedia resolves)
│   │         - room_connected (when RoomEvent.Connected fires)
│   │
│   └── send_session_context
│           attributes: client_action.action="session_context",
│                       client_action.direction="app_to_agent"
│           log events (correlated via span context):
│             - published { client_action.input: <scenario context JSON> }
│
├── conversation
│   │   attributes: session.id, scenario.id
│   │   starts: after setup completes (room connected + context sent)
│   │   ends: when endSimulation() is called
│   │
│   │   log events (one per transcript turn, correlated via span context):
│   │     - transcript_turn { role: "agent", text: "Hi, how can I help?" }
│   │     - transcript_turn { role: "user", text: "I have a problem with..." }
│   │     - transcript_turn { role: "agent", text: "Let me look into that" }
│   │     - ...
│   │     - end_simulation_received { source: "agent" }   (when agent sends end_simulation)
│   │     - end_simulation_received { source: "user" }    (when user clicks End button)
│   │
│   │   (the conversation span covers the ENTIRE dialogue duration)
│
└── cleanup
    │   attributes: session.id
    │   starts: when endSimulation() runs
    │   ends: when transcript stored + room disconnected
    │
    └── fetch POST /api/transcript
            attributes: http.method, http.url, http.status_code
```

**Key points:**
- `room_connect` span covers `getUserMedia()` + `room.connect()` + mic enable. This is the latency users feel.
- `conversation` span is long-lived (30s–5min). Transcript turns are **log records** correlated to this span via context — not child spans or span events.
- `send_session_context` is a real span because it wraps the publishData call in the setup phase. It's short but meaningful in context.
- `cleanup` is separate from conversation so the trace timeline shows the transition clearly.

### 3.2 Feedback Phase

```
feedback (root span)
│   attributes: session.id, scenario.id
│
└── fetch POST /api/coaching
        attributes: http.method, http.url, http.status_code
        log events (correlated via span context):
          - evaluation_received { overall_score: 7.8, categories_count: 5 }
```

**Key points:**
- This is intentionally minimal — it's one API call (2–10s for OpenAI).
- The `evaluation_received` event captures the score so it's visible in the trace without digging into network payloads.

### 3.3 Coaching Phase

```
coaching (root span)
│   attributes: session.id, scenario.id, coaching.iteration (1, 2, 3...)
│
├── setup
│   │
│   ├── fetch POST /api/coaching-session
│   │       attributes: http.method, http.url, http.status_code
│   │
│   └── room_connect
│           attributes: livekit.url
│           starts: getUserMedia() called
│           ends: room Connected event fires
│           log events (correlated via span context):
│             - media_acquired
│             - room_connected
│
├── data_exchange
│   │   starts: room connected
│   │   ends: both payloads published
│   │
│   │   log events (correlated via span context):
│   │     - feedback_data_sent { client_action.input: <feedback JSON summary> }
│   │     - transcript_data_sent { client_action.input: <transcript entry count> }
│
├── conversation
│   │   attributes: session.id, scenario.id
│   │   starts: after data_exchange completes
│   │   ends: when endCoachingCall() is called
│   │
│   │   log events (correlated via span context):
│   │     - transcript_turn { role: "agent", text: "Let's review your opening..." }
│   │     - transcript_turn { role: "user", text: "OK, should I try again?" }
│   │     - ...
│   │     - end_conversation_received { source: "agent" }
│
└── cleanup
        starts: when endCoachingCall() runs
        ends: room disconnected
```

**Key points:**
- `coaching.iteration` attribute on the root span distinguishes first attempt (1) from restarts (2, 3, ...). The frontend tracks a counter.
- `data_exchange` replaces the old `feedback_data` and `transcript_data` spans. The individual sends become log-record events on a parent that covers both.
- For `feedback_data_sent`, the input attribute should be a **summary** (overall score + category count), not the entire JSON. Store the full payload only if it's under 1KB.

---

## 4. Browser Telemetry API

Replace the current `otel-browser.js` exports with a cleaner API. The module should expose these functions on `window.__otel`:

### `ready` — Promise<void>
Resolves when the tracer is initialized. All other functions are safe to call before this resolves (they'll use noop tracer).

### `startPhase(sessionId, phase, attributes)` → PhaseContext
Creates a root span for the phase. Returns a context object used by all other calls.

```js
// Returns: { rootSpan, ctx, createChildSpan, addEvent, end }
const sim = window.__otel.startPhase(sessionId, "simulation", {
  "scenario.id": scenario.id,
  "scenario.title": scenario.title,
});
```

### `PhaseContext.createChildSpan(name, attributes)` → Span
Creates a child span parented to the phase root, within the phase trace context. Caller is responsible for calling `span.end()`.

```js
const setupSpan = sim.createChildSpan("setup");
// ... do work ...
setupSpan.end();
```

### `PhaseContext.addEvent(name, attributes)`
Emits a log record with `event.name` set, correlated to the phase root span via active context. Use for lifecycle events at the phase level.

```js
sim.addEvent("evaluation_received", { overall_score: 7.8 });
```

### `PhaseContext.end()`
Ends the root span and cleans up the phase context.

```js
sim.end();
```

### `tracedFetch(url, options, phaseContext)` → Promise<Response>
Creates a child span for the fetch call, injects `traceparent` header, records `http.status_code`. Parented to the phase context.

```js
const resp = await window.__otel.tracedFetch("/api/session", { method: "POST", ... }, sim);
```

### Usage pattern in index.html

```js
// Start simulation
const sim = window.__otel.startPhase(sessionId, "simulation", {
  "scenario.id": scenario.id,
});

// Setup block
const setupSpan = sim.createChildSpan("setup");
const resp = await window.__otel.tracedFetch("/api/session", opts, sim);

const connectSpan = sim.createChildSpan("room_connect", { "livekit.url": url });
await navigator.mediaDevices.getUserMedia({ audio: true });
connectSpan.addEvent("media_acquired");
await room.connect(url, token);
connectSpan.addEvent("room_connected");
await room.localParticipant.setMicrophoneEnabled(true);

const ctxSpan = sim.createChildSpan("send_session_context", {
  "client_action.direction": "app_to_agent",
});
await room.localParticipant.publishData(payload, { topic: "client_actions" });
ctxSpan.addEvent("published", { "client_action.input": JSON.stringify(scenarioCtx) });
ctxSpan.end();
connectSpan.end();
setupSpan.end();

// Conversation — long-lived span
const convSpan = sim.createChildSpan("conversation", { "scenario.id": scenario.id });

// On each transcript turn received:
convSpan.addEvent("transcript_turn", { role: "agent", text: msgText });

// On simulation end:
convSpan.addEvent("end_simulation_received", { source: "agent" });
convSpan.end();

// Cleanup
const cleanupSpan = sim.createChildSpan("cleanup");
await window.__otel.tracedFetch("/api/transcript", opts, sim);
cleanupSpan.end();
sim.end();
```

> **Note:** `addEvent` emits a log record via the Logs API (not `span.addEvent()`). The name "addEvent" is kept for ergonomics — internally it calls `logger.emit()` with `event.name` and the current span context.

### What gets removed

- `startClientActionSpan()` — removed. Client actions become either child spans (if they wrap real work) or log records (if they're point-in-time).
- `getOrCreateSessionContext()` / `endSessionContext()` — replaced by `startPhase()` / `PhaseContext.end()`.
- The existing broken `emitLog()` — replaced by a working implementation inside `PhaseContext.addEvent()` and `ChildSpan.addEvent()`.

---

## 5. Attribute Conventions

All spans and events, frontend and backend, use these attribute names:

| Attribute | Type | Where | Example |
|-----------|------|-------|---------|
| `session.id` | string | All spans | `"returns-1709845200000"` |
| `session.phase` | string | All spans | `"simulation"`, `"feedback"`, `"coaching"` |
| `scenario.id` | string | Phase roots, conversation spans, backend route spans | `"returns"` |
| `scenario.title` | string | Phase root only | `"Product Return Request"` |
| `scenario.difficulty` | string | Phase root only | `"medium"` |
| `coaching.iteration` | int | Coaching root span | `1`, `2`, `3` |
| `client_action.action` | string | Client action spans/log records | `"session_context"`, `"feedback_data"` |
| `client_action.direction` | string | Client action spans/log records | `"app_to_agent"`, `"agent_to_app"` |
| `client_action.input` | string | Client action log records | JSON payload (truncated to 4KB) |
| `http.method` | string | Fetch spans | `"POST"` |
| `http.url` | string | Fetch spans | `"/api/session"` |
| `http.status_code` | int | Fetch spans | `200` |
| `livekit.url` | string | room_connect spans | `"wss://..."` |
| `agent.name` | string | Backend ensure_agent span | `"VoiceCoach Customer"` |
| `agent.id` | string | Backend ensure_agent span, vb_token_request span | `"abc-123"` |
| `participant.name` | string | Backend vb_token_request span | `"Trainee"` |
| `overall_score` | float | evaluation_received event | `7.8` |

### Transcript turn log record attributes

Log records for transcript turns carry:

| Attribute | Type | Example |
|-----------|------|---------|
| `role` | string | `"agent"`, `"user"` |
| `text` | string | `"Thank you for calling..."` |

No `transcript.` prefix needed — these are attributes on a `transcript_turn` log record, so the event name provides context.

---

## 6. Backend Changes Needed

1. **Add `agent.id` to `vb_token_request` span.** Currently the span has `participant.name` but not which agent the token is for. Add:
   ```python
   span.set_attribute("agent.id", _sim_agent_id or _coach_agent_id)
   ```

2. **Add `scenario.id` to `create_coaching_session` span.** The request carries `scenario_id` but the span doesn't record it:
   ```python
   span.set_attribute("scenario.id", req.scenario_id or "")
   ```

3. **Add span around VB CLI calls.** `_run_vb()` and `_run_vb_json()` should be wrapped:
   ```python
   with tracer.start_as_current_span("vb_cli", attributes={"vb.command": " ".join(args[:2])}):
   ```

4. **Propagate `session.id` consistently.** The backend receives `trace_session_id` from the frontend. Set it on all spans where available, not just some:
   ```python
   if req.trace_session_id:
       span.set_attribute("session.id", req.trace_session_id)
   ```
   This is already done on most endpoints but missing on `/api/scenarios`.

5. **Add `session.phase` attribute to backend spans.** The backend knows which phase it's serving based on the endpoint:
   - `/api/session` → `"simulation"`
   - `/api/transcript` → `"simulation"`
   - `/api/coaching` → `"feedback"`
   - `/api/coaching-session` → `"coaching"`

---

## 7. Key Decision: Log Records for Events (Not Span Events)

**Decision: Use OTel log records (Logs API) for transcript turns, lifecycle events, and client action annotations. Log records are automatically correlated with the active span via context. Keep the LoggerProvider + OTLPLogExporter in the browser bundle.**

### Rationale

OpenTelemetry is [officially deprecating `Span.AddEvent`](https://opentelemetry.io/blog/2026/deprecating-span-events/) in favor of log-based events emitted via the Logs API. The community position: "events are logs with names emitted via the Logs API, correlated with traces and metrics through context." New code should use the Logs API; `span.addEvent()` will be phased out.

This aligns with what we need:

| | Log Records (Logs API) | Span Events (deprecated) |
|---|---|---|
| OTel direction | ✅ Recommended for new code | ⚠️ Deprecated (`Span.AddEvent` being phased out) |
| Carry trace context | ✅ Automatic via active context | ✅ Belong to parent span |
| Aspire dashboard support | ✅ `/v1/logs` OTLP HTTP endpoint | ✅ Inline in trace detail |
| Semantic fit | ✅ Events are named log records | ❌ Deprecated concept |
| Future-proof | ✅ Aligns with OTel roadmap | ❌ Will require migration later |
| Bundle size impact | ~15KB (LoggerProvider + exporter) | 0KB (in trace SDK) |

The bundle size cost (~15KB) is worth paying to align with the direction OTel is moving. Building on a deprecated API would mean migrating later anyway.

### What uses log records

| Event | `event.name` | Key attributes | Emitted during |
|---|---|---|---|
| Transcript turn | `transcript_turn` | `role`, `text` | conversation span |
| Simulation started | `simulation_started` | `session.id` | simulation root |
| Room connected | `room_connected` | `livekit.url` | room_connect span |
| Room disconnected | `room_disconnected` | `session.id` | conversation span |
| End simulation received | `end_simulation_received` | `source` | conversation span |
| Coaching started | `coaching_started` | `session.id`, `coaching.iteration` | coaching root |
| Feedback data sent | `feedback_data_sent` | `client_action.input` | data_exchange span |
| Transcript data sent | `transcript_data_sent` | `client_action.input` | data_exchange span |
| End conversation received | `end_conversation_received` | `source` | conversation span |
| Evaluation received | `evaluation_received` | `overall_score`, `categories_count` | feedback fetch span |

All log records are emitted while a span is active, so they automatically pick up trace context (`trace_id`, `span_id`). The Aspire dashboard can correlate them.

### Implementation note

The original `emitLog()` in `otel-browser.js` had two bugs that prevented log records from reaching Aspire:
1. **`LoggerProvider.addLogRecordProcessor()` does not exist** in `@opentelemetry/sdk-logs@0.214.0`. The API requires processors to be passed in the constructor via the `processors` option: `new LoggerProvider({ resource, processors: [...] })`.
2. **The entire OTel init crashed** because the `.catch()` handler set `logger = null`, disabling all telemetry (traces AND logs) when the LoggerProvider call failed.

Both are fixed. Log records now flow from the browser to Aspire's `/v1/logs` OTLP HTTP endpoint and appear in the structured logs view correlated to their parent traces.

---

## Appendix: Implementation Status

All items are complete:

- [x] **Rewrite `otel-browser.js`** — new API (`startPhase`, `PhaseContext`, `tracedFetch`), `LoggerProvider` bug fixed, `SimpleLogRecordProcessor` with constructor `processors` option.
- [x] **Refactor `index.html` telemetry calls** — old helpers removed (`reportTelemetry`, `startClientActionSpan`, `otelFetch`), replaced with phase-based API. `room_connect` spans, long-lived `conversation` span with log-record events.
- [x] **Backend attribute additions** — `agent.id` on `vb_token_request`, `scenario.id` on `create_coaching_session`, `session.phase` on all route handlers, `vb_cli` spans wrapping all VB CLI calls.
- [x] **Validated in Aspire** — full flow exercised, conversation turns visible as structured logs correlated to traces, room connection latency visible in trace waterfall, coaching iteration tracking works.

### Known improvements for future work

- **Transcript text truncation** — long utterances are cut off in log record attributes due to OTel attribute length limits.
- **Cross-phase trace linking** — simulation, feedback, and coaching are separate traces sharing `session.id` but not linked via span links.
- **Turn indexing** — `transcript_turn` log records lack a `turn.index` attribute for ordering.
- **Agent silence detection** — no event fires when the coaching agent stops responding mid-conversation.
