# Squad Decisions

## Active Decisions

### 2026-03-25: DIRECTIVE — Research Before Implementation
**By:** Drew Robbins
**What:** All agents MUST consult official documentation before writing code or making changes. No trial and error as a starting point. Look up Aspire docs (aspire.dev, learn.microsoft.com/dotnet/aspire), SDK docs, NuGet/npm package docs, and framework references BEFORE attempting implementation. Do not guess at APIs, config patterns, or integrations — read the docs first. Use the Aspire MCP tools (`list integrations`, `get integration docs`) and `fetch_webpage` for official documentation when needed.
**Why:** The team has been wasting time on trial-and-error and recreating things that already exist. Research-first reduces churn and improves accuracy.
**Scope:** Applies to ALL agents, ALL tasks. This is a standing directive.

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
# Decision: .NET Aspire Orchestration for Polyglot Setup

**Context**: Setting up a Python backend and TS/React frontend.
**Decision**: We will use .NET Aspire (`dotnet new aspire-apphost`) for local orchestration of the polyglot stack.
**Rationale**: .NET Aspire provides a single `Program.cs` that can start the Npm app and Python app (`AddNpmApp` and `AddPythonApp`) together, injecting environment variables and references seamlessly.
# Project Structure Decision
We decided to store all code under src/, with backend in Python and frontend in React/TS.
# Infrastructure Decisions

- **Aspire Landing Zone**: Created Azure Container Apps Environment, Log Analytics Workspace, and Application Insights via Bicep. This provides the standard managed environment architecture suitable for .NET Aspire deployments to Azure.
- **GitHub Actions Security**: Designed the deploy.yml workflow to use Azure AD Workload Identity Federation (OIDC) via `azure/login@v2`. This eliminates the need to manage secret keys/passwords for deployment credentials.
- **Bicep Modularity**: Kept `main.bicep` as a subscription-scoped entry point to handle Resource Group creation, while delegating the actual service provisioning to `resources.bicep`.
### $(date -u +"%Y-%m-%dT%H:%M:%SZ"): User directive
**By:** Drew Robbins (via Copilot)
**What:** All code should be under the `src` directory.
**Why:** User request — captured for team memory


## Merged Decisions (2026-03-23T05:13:48Z)
# Local Dev Certificates Strategy for Polyglot Apps

## Context
When running .NET Aspire locally with a Python backend and TypeScript/React frontend, we need trusted HTTPS certificates to enable secure inter-service communication (e.g. gRPC or secure REST) and a clean developer experience without browser warnings.

## Mechanism
1. The `.devcontainer/devcontainer.json`'s `postStartCommand` provisions a trusted local certificate via `dotnet dev-certs https --trust`.
2. It immediately exports these certificates into the `tmp/` root directory in PEM format (`tmp/localhost.crt` and `tmp/localhost.key`).

## Usage by Subsystems

### Backend (Python)
- Python applications (such as FastAPI or Flask) can load these directly for their SSL context.
- E.g., for Uvicorn: run with `--ssl-keyfile ../../tmp/localhost.key --ssl-certfile ../../tmp/localhost.crt` (adjust relative path to workspace root).
- If acting as a client, ensure `REQUESTS_CA_BUNDLE` or `SSL_CERT_FILE` points to the exported certificate, or the OS trust store is updated (which the devcontainer already attempts).

### Frontend (TypeScript / React / Vite)
- The frontend dev server (like Vite or Webpack) can refer to these certificates to launch on `https://localhost`.
- For Vite: configure `server.https.key` and `server.https.cert` pointing to `tmp/localhost.key` and `tmp/localhost.crt`, respectively.

This ensures all components within Aspire share the same trusted certificate chain locally.


# Decision: Add python3-venv to devcontainer

**Date:** 2026-03-23T05:21:07Z
**Agent:** Browning

## Context
The user experienced an error `/usr/bin/python3: No module named venv` when running the application. The default `dotnet:10.0` dev container lacks the `python3-venv` package.

## Decision
Added `sudo apt-get update && sudo apt-get install -y python3-venv` to the `onCreateCommand` in `.devcontainer/devcontainer.json`. This ensures any future rebuilds will include the package out of the box so developers do not need to intervene manually.

### 2026-03-23T06:00:00Z: Phase 0 — Environment & Tooling Setup
**By:** Browning (requested by Drew Robbins)
**What:** Vocal Bridge SDK (v0.14.0) installed in backend venv. VB_API_KEY passed to backend via Aspire AppHost config (builder.Configuration, not hardcoded). .env.example created at root.
**Why:** Phase 0 prerequisite for voice agent integration. Key is read from environment/config at runtime — no secrets in source.

### 2026-03-23: VoiceCoach MVP Plan — Key Architectural Recommendations
**By:** Cobb (Product Manager)
**What:** Created `docs/voicecoach-plan.md` with 5 key technical decisions flagged for team consensus:
1. **Two-agent approach (Option B):** Vocal Bridge for simulation (voice), direct LLM API for coaching (text). Simplest path.
2. **Transcript handoff via frontend accumulation (Option A):** Frontend collects from LiveKit events, POSTs to backend. Matches helloworld pattern.
3. **Scenario injection via `session_context` client action (Option A):** Established Vocal Bridge pattern. Base prompt has manual/catalog, session_context injects persona.
4. **Coaching is text-only for MVP (Option A):** Structured JSON output, not voice-interactive. Can upgrade later.
5. **LLM provider for coaching: deferred to Yusuf** — needs structured JSON output, citation accuracy, consistent scoring.
**Why:** These decisions shape the entire implementation. The plan is structured so work can begin on Phases 0 and 1 immediately while decisions 1–4 are reviewed by the team.

### 2026-03-23: Two Vocal Bridge Agents — Separate API Keys
**By:** Drew Robbins
**What:** VoiceCoach requires TWO separate Vocal Bridge agents, each with its own API key:
1. **Simulation Agent** — Runs the live voice conversation, plays the AI customer persona
2. **Coaching Agent** — Receives the completed transcript, evaluates against the employee manual and rubric
Each agent is created independently via `vb create` and gets its own `VB_API_KEY` (e.g., `VB_SIM_API_KEY`, `VB_COACH_API_KEY`).
**Why:** The PRD specifies a two-agent architecture where simulation and coaching are independent — different system prompts, different tuning, different client actions.

### 2026-03-23: Phase 1 Agent Design Complete
**By:** Cobb (Product Manager)
**What:** Created all 6 agent design artifacts under `src/backend/agents/`. Both system prompts include the COMPLETE employee manual (§1–§5) and product catalog (8 SKUs) verbatim from the PRD. Coaching rubric has 8 categories scored 1–10.
**Why:** Phase 1 deliverable. Backend implementation (Phase 2) can begin — Yusuf has everything needed to wire up both agents.

### 2026-03-23: Frontend architecture — plain HTML SPA with API proxy
**By:** Eames (Frontend Dev)
**What:** Built VoiceCoach frontend as a single `index.html` with inline CSS + vanilla JS (no React, no build step). Express server.js proxies `/api/*` to the Python backend. LiveKit SDK loaded from CDN.
**Why:** Hackathon speed — zero build tooling, instant iteration, matches the helloworld reference pattern exactly.

### 2026-03-23: Backend API endpoints built
**By:** Yusuf
**What:** Built all 4 API endpoints in src/backend/main.py — scenarios, session, transcript, coaching. Coaching falls back to mock response when OPENAI_API_KEY is not set. Used httpx (async) instead of requests for VB token call.
**Why:** Phase 2 of hackathon build — backend must be ready for frontend integration.

### 2026-03-23: Dynamic VB Agent Reconfiguration Per Session
**By:** Yusuf
**What:** Reconfigure the VB agent at request time using the `vb` CLI before each token call. Each `/api/session` call rebuilds the full prompt from simulation_prompt.md + employee manual + scenario context, sets scenario-specific voice and greeting. Separate `/api/coaching-session` endpoint for coaching mode.
**Why:** Single VB agent instance, reconfigured dynamically — simplest approach for hackathon, avoids managing multiple agents.

### 2026-03-23: Coaching Voice Call as Embedded Section
**By:** Eames (Frontend)
**What:** Embedded the coaching voice call UI directly within `screen-coaching` as a collapsible section that appears after clicking "Start Coaching Session." Coaching transcript, visualizer, and controls sit below the scores.
**Why:** Keeps user's scores visible during coaching conversation. Avoids extra navigation step. Reuses existing LiveKit connection pattern with separate `coachingRoom` instance.

### 2026-03-25: OpenTelemetry tracing instrumentation for Python backend
**By:** Yusuf (Backend Developer)
**What:** Added full OTel tracing to `src/backend/main.py` alongside the existing OTel logging. TracerProvider uses the same OTLP endpoint/protocol detection as LoggerProvider. Auto-instrumented FastAPI (inbound) and httpx (outbound) via their respective OTel instrumentation libraries. Added custom spans to all key business operations: agent initialization, session creation, token requests, transcript storage, coaching evaluation, and the OpenAI call. All spans record exceptions and set ERROR status on failure.
**Why:** Traces were missing from the Aspire dashboard — only logs were flowing. This gives full distributed tracing visibility into request flows, agent setup, and external API calls.

### 2026-03-25: OTEL Infrastructure Verification — No AppHost Changes Required
**By:** Browning
**What:** Verified that the Aspire AppHost (SDK 13.1.3) already provides complete OTLP telemetry infrastructure for the Python backend. No changes to Program.cs or the csproj are needed. Aspire auto-injects all standard `OTEL_*` environment variables into both backend and frontend resources.
**Why:** Confirmed by inspecting live resource environment variables and structured logs on the running Aspire instance. Frontend Node.js OTel instrumentation deferred as a future enhancement.

### 2026-03-25: Telemetry endpoint for frontend conversation events
**By:** Yusuf (requested by Drew Robbins)
**What:** Added POST /api/telemetry (batch) and POST /api/telemetry/event (single) to src/backend/main.py. Frontend can now report LiveKit room events (transcript turns, client actions like session_context/end_simulation/feedback_data, and session lifecycle events) to the backend, which creates OpenTelemetry spans that appear in Aspire traces.
**Why:** Conversation events happen directly between the browser and Vocal Bridge via LiveKit — they never touch our backend. Without this endpoint, the entire voice conversation is invisible in Aspire. Now the frontend can POST events as they happen, and they show up as traced spans alongside our existing backend traces.
**Validation:** event_type must be one of: client_action, transcript_turn, session_lifecycle. Unknown types return 422.

## Merged Decisions (2026-03-26T000000Z)

### 2026-03-25: Enable OTLP/HTTP endpoint for browser telemetry
**By:** Browning (Build & Infrastructure)
**What:** Added `ASPIRE_DASHBOARD_OTLP_HTTP_ENDPOINT_URL` to launchSettings.json (port 21265/19071). Injected `OTEL_EXPORTER_OTLP_HTTP_ENDPOINT` to frontend resource in Program.cs. Backend continues using auto-injected gRPC vars. No manual CORS needed.
**Why:** Aspire dashboard only exposes OTLP gRPC by default. Browser OTel SDK sends HTTP protobuf/JSON, which gets 403 on the gRPC endpoint. The HTTP endpoint enables browser → Aspire trace flow.

### 2026-03-25: Client telemetry moved from Python backend to Node.js frontend
**By:** Eames (Frontend Dev)
**What:** Replaced the custom `/api/telemetry/event` REST proxy approach (browser → Node proxy → Python backend → OTel) with native OpenTelemetry on the Node.js frontend server (browser → Node `/telemetry` → Aspire OTLP collector directly). The frontend server already receives `OTEL_*` env vars from Aspire, so it's the natural owner of client telemetry spans.
**Why:** Eliminates an unnecessary network hop through the Python backend for telemetry. The Node.js server is the first server-side process that receives browser events — it should own the span creation.

### 2026-03-25: Frontend telemetry payload summaries + client action ordering fix
**By:** Eames (Frontend Dev)
**What:** `reportTelemetry` for `feedback_data` now includes `overall_score`, `scores_count`, `improvement_areas_count`, `has_coaching_dialogue`. For `transcript_data`, includes `transcript_count`. Added 100ms delivery delay for ordering reliability.
**Why:** Client action spans had no payload data to inspect, and both actions arrived at the same millisecond risking out-of-order processing.

### 2026-03-25: Removed client telemetry relay from Python backend
**By:** Yusuf
**What:** Deleted all browser-facing telemetry code from `src/backend/main.py`: `TELEMETRY_DEBUG`, `VALID_EVENT_TYPES`, telemetry models, phase inference, and `/api/telemetry` + `/api/telemetry/event` endpoints.
**Why:** Client telemetry moved to the Node.js frontend server. Backend no longer needs to proxy browser events.

### 2026-03-26: Telemetry Architecture — Span Events Over Logs, Structured Phase API
**By:** Arthur (Lead), synthesizing inputs from Yusuf, Eames, Browning
**What:**
1. Browser OTel logs replaced by span events (logs don't reach Aspire dashboard from browser).
2. LoggerProvider + OTLPLogExporter removed from browser bundle (saves ~15KB).
3. New frontend API: `startPhase()` → `PhaseContext` with `createChildSpan()`, `addEvent()`, `end()`.
4. Conversation turns are span events on a long-lived `conversation` span.
5. Client actions that wrap real work stay as spans; point-in-time actions become span events.
6. New `room_connect` span covering getUserMedia() + room.connect().
7. `coaching.iteration` attribute for restart tracking.
8. Standardized attribute names across frontend and backend.
9. Backend additions: `agent.id` on `vb_token_request`, `scenario.id` on `create_coaching_session`, span around VB CLI calls, `session.phase` on all backend spans.
**Why:** Browser logs invisible in Aspire (confirmed by Browning). Organic growth of three telemetry mechanisms was confusing and produced misleading traces. This architecture makes all conversation data visible in Aspire trace detail.
**Reference:** `docs/telemetry-architecture.md`

