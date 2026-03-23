# VoiceCoach — MVP Implementation Plan

**Author:** Cobb (Product Manager)
**Date:** March 2026
**Status:** Draft — Ready for Team Review

---

## 1. Executive Summary

VoiceCoach is an AI-powered voice simulation tool that trains retail customer service reps through realistic conversations with an AI customer, followed by automated coaching grounded in company procedures. A trainee picks a scenario, conducts a live voice conversation with a Vocal Bridge–powered AI customer agent, and then receives structured coaching feedback that cites specific sections of the employee manual.

We are building this on top of **Vocal Bridge** (the voice agent platform demonstrated in `docs/helloworld/`) and our existing **Aspire-orchestrated polyglot stack** (Python backend + TypeScript frontend, orchestrated by .NET Aspire in `src/VoiceProject.AppHost/`).

**Core loop (under 10 minutes per session):**

1. **Select Scenario** — Trainee picks Easy / Medium / Hard
2. **Voice Simulation** — Live conversation with an AI customer via Vocal Bridge WebRTC
3. **Coaching Review** — A separate AI evaluates the transcript against the employee manual

**Key differentiator:** Both agents share the same employee manual. The simulation agent uses it to *test* whether the trainee follows procedures. The coaching agent uses it to *cite* specific sections when delivering feedback. This makes training consistent, auditable, and tied to actual company standards.

---

## 2. Architecture Overview

### How VoiceCoach Maps to the Helloworld Patterns

The `docs/helloworld/` directory is our reference implementation for Vocal Bridge integration. Every VoiceCoach component has a direct counterpart:

| Helloworld Component | VoiceCoach Equivalent | Notes |
|---|---|---|
| `config.py` — `AgentConfig` dataclass | `src/backend/agents/config.py` — `SimulationAgentConfig` + `CoachingAgentConfig` | Two configs instead of one. Each agent has its own prompt, style, client actions, and scenario-specific overrides. |
| `setup_agent.py` — creates agent via `vb` CLI | `src/backend/agents/setup_agents.py` — creates both agents | Simulation Agent is voice-interactive (like helloworld). Coaching Agent may be text-only or voice, TBD. |
| `client_actions.json` — `send_document`, `end_conversation`, `session_context` | `src/backend/agents/client_actions_sim.json` + `client_actions_coach.json` | Simulation: `end_simulation` (triggers transcript handoff), `session_context` (scenario selection). Coaching: `send_evaluation`, `send_document`, `end_conversation`. |
| `server.py` — token proxy + static file server | `src/backend/main.py` — FastAPI with `/api/session`, `/api/scenarios`, `/api/coaching` | Expands from 1 endpoint to several. Token proxy pattern stays the same. |
| `web_embed/index.html` + `app.js` — LiveKit WebRTC client | `src/frontend/public/` — React/TS app with scenario picker, simulation view, coaching results | Three screens instead of one. LiveKit connection pattern from `app.js` is reused. |
| `vb-agent-prompt.md` — system prompt | Two prompt files: simulation agent prompt + coaching agent prompt | Simulation prompt includes persona + manual + catalog + actor strategy. Coaching prompt includes rubric + manual + scoring template. |
| `run_agent.py` — CLI session launcher | Not needed for MVP — web-only | Could be useful for debugging. |

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   .NET Aspire AppHost                │
│                  (src/VoiceProject.AppHost)           │
│                                                       │
│  ┌──────────────┐    references    ┌──────────────┐  │
│  │   Frontend    │◄───────────────►│   Backend     │  │
│  │  (npm/TS)     │                 │  (Python)     │  │
│  └──────┬───────┘                  └──────┬───────┘  │
└─────────┼──────────────────────────────────┼─────────┘
          │                                  │
          │ HTTPS                             │ HTTPS
          ▼                                  ▼
┌──────────────────┐              ┌──────────────────────┐
│  Browser Client   │              │ Vocal Bridge API      │
│  - Scenario Picker│              │ POST /api/v1/token    │
│  - LiveKit Room   │              │ → { livekit_url,      │
│  - Transcript     │              │     token,            │
│  - Coaching View  │              │     room_name }       │
└──────────────────┘              └──────────────────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │  LiveKit (WebRTC) │
                                  │  Voice Transport  │
                                  └──────────────────┘
```

### Data Flow

1. **Scenario Selection** → Frontend sends scenario ID to Backend
2. **Token Acquisition** → Backend calls Vocal Bridge `/api/v1/token` with `X-API-Key` header (pattern from `server.py` lines 73–100)
3. **Voice Session** → Frontend connects LiveKit Room with token (pattern from `app.js`)
4. **Transcript Capture** → LiveKit `send_transcript` events captured in real-time (pattern from `app.js` `appendTranscript`)
5. **Simulation End** → Agent fires `end_simulation` client action → Frontend sends full transcript to Backend
6. **Coaching** → Backend invokes Coaching Agent (or direct LLM call) with transcript + manual + rubric
7. **Results Display** → Frontend renders structured coaching evaluation with scores and manual citations

---

## 3. Work Phases

### Phase 0: Environment & Tooling Setup

**Goal:** Prove the Vocal Bridge toolchain works in our environment. Every team member can run the helloworld agent.

**Dependencies:** None (starting point)

**Duration target:** First work session

#### Tasks

- [ ] **0.1 — Install Vocal Bridge CLI and dependencies**
  - **Description:** Install the `vb` CLI tool (v0.7.1+) via `uv pip install vocal-bridge`. Verify with `vb --version`. Follow `docs/helloworld/requirements.txt` pattern.
  - **Owner:** Browning
  - **Dependencies:** None
  - **Acceptance Criteria:** `vb --version` returns 0.7.1+. `vb auth login` succeeds.

- [ ] **0.2 — Obtain Vocal Bridge API key**
  - **Description:** Sign up at vocalbridgeai.com/auth/signup. Get a `vb_`-prefixed API key. Store in `.env` (never commit). Pattern: `docs/helloworld/README.md` Step 2.
  - **Owner:** Browning
  - **Dependencies:** None
  - **Acceptance Criteria:** Valid `VB_API_KEY=vb_...` in `.env`. Key works with `vb auth login`.

- [ ] **0.3 — Run the helloworld agent end-to-end**
  - **Description:** Follow `docs/helloworld/README.md` Quick Start: create venv, install deps, run `setup_agent.py` to create the agent, then `python server.py` to serve the web embed. Open browser, start a voice conversation, verify audio works both ways.
  - **Owner:** Browning
  - **Dependencies:** 0.1, 0.2
  - **Acceptance Criteria:** Helloworld web embed loads at localhost:8000. User can speak to the agent. Agent responds with voice. Transcript appears in real-time. `send_document` client action works.

- [ ] **0.4 — Configure VB_API_KEY in Aspire AppHost**
  - **Description:** Add `VB_API_KEY` as a parameter/secret in `Program.cs` and pass it to the backend via `.WithEnvironment()`. Ensure it's NOT committed to source control.
  - **Owner:** Browning
  - **Dependencies:** 0.2, 0.3
  - **Acceptance Criteria:** Backend receives `VB_API_KEY` env var when launched via `aspire run`. Key is loaded from user secrets or `.env`, not hardcoded.

---

### Phase 1: Agent Design

**Goal:** Design both Vocal Bridge agents with complete system prompts, client actions, and scenario configurations. This is the *product design* phase — no code yet, just agent specs.

**Dependencies:** Phase 0 complete (team understands the Vocal Bridge patterns)

#### Tasks

- [ ] **1.1 — Design Simulation Agent system prompt**
  - **Description:** Write the full system prompt for the AI customer agent. Must include: (a) the complete Northfield employee manual (§1–§5 from PRD §3), (b) the product catalog (PRD §4, 8 SKUs), (c) per-scenario persona instructions, (d) actor strategy rules (how to test trainee compliance), (e) instructions to use `end_simulation` client action when conversation ends, (f) instructions to respond to `session_context` with the selected scenario. Pattern: `docs/helloworld/vb-agent-prompt.md` but much more complex.
  - **Owner:** Cobb
  - **Dependencies:** 0.3 (must have seen helloworld prompt pattern)
  - **Acceptance Criteria:** Prompt covers all 3 scenarios. Each scenario's "Manual Sections Tested" (PRD §5) are explicitly addressed. Prompt instructs agent to test trainee without being obvious. Prompt fits within Vocal Bridge context limits.

- [ ] **1.2 — Design Coaching Agent system prompt**
  - **Description:** Write the full system prompt for the coaching evaluator. Must include: (a) the same employee manual, (b) scoring rubric with categories (Greeting Protocol, Active Listening, Product Knowledge, De-escalation, Goodwill, Escalation Handling, Policy Compliance, Closing Protocol), (c) instructions to cite specific manual sections (e.g., "Per §2.1..."), (d) instructions to produce structured JSON output with scores + per-category feedback + improvement areas. Pattern: PRD §6 "Coaching Evaluation: Example Output".
  - **Owner:** Cobb
  - **Dependencies:** 1.1
  - **Acceptance Criteria:** Rubric covers all categories from PRD §6 scoring table. Output format includes numeric scores per category, manual section citations, and 2–3 key improvement areas. Example output matches PRD §6 quality.

- [ ] **1.3 — Define client actions for Simulation Agent**
  - **Description:** Create `client_actions_sim.json` following the pattern in `docs/helloworld/client_actions.json`. Actions needed: `end_simulation` (agent_to_app — signals conversation end and triggers transcript capture), `session_context` (app_to_agent, behavior: "respond" — passes selected scenario ID/persona at session start).
  - **Owner:** Cobb
  - **Dependencies:** 0.3
  - **Acceptance Criteria:** JSON structure matches helloworld format. Each action has name, description, direction. `session_context` has `behavior: "respond"`.

- [ ] **1.4 — Define client actions for Coaching Agent**
  - **Description:** Create `client_actions_coach.json`. Actions needed: `send_evaluation` (agent_to_app — sends structured coaching JSON to frontend), `send_document` (agent_to_app — sends text summaries), `end_conversation` (agent_to_app — closes coaching session), `session_context` (app_to_agent — passes transcript + scenario context).
  - **Owner:** Cobb
  - **Dependencies:** 1.2
  - **Acceptance Criteria:** JSON structure matches helloworld format. `send_evaluation` action is defined for structured coaching data delivery.

- [ ] **1.5 — Define scenario configuration data**
  - **Description:** Create a structured data file (`scenarios.json` or Python dataclass) containing all 3 scenarios from PRD §5: (1) Simple Product Inquiry / Easy / Sarah, (2) Multi-Issue Order Problem / Medium / David, (3) Angry Customer Escalation / Hard / Karen. Each entry includes: ID, title, difficulty, customer_name, one-line description (visible to trainee), full persona + goal + behavior + actor_strategy (injected into agent prompt), manual_sections_tested list.
  - **Owner:** Cobb
  - **Dependencies:** 1.1
  - **Acceptance Criteria:** All 3 scenarios from PRD §5 fully represented. Trainee-visible fields are separate from agent-only fields. Data structure supports the `session_context` client action.

- [ ] **1.6 — Create Vocal Bridge agent configurations**
  - **Description:** Create `AgentConfig` dataclasses (following `docs/helloworld/config.py` pattern) for both agents. Simulation Agent: name="VoiceCoach Customer", style="Conversational", appropriate max_call_duration (10 min), max_history_messages. Coaching Agent: name="VoiceCoach Coach", style="Professional", shorter duration.
  - **Owner:** Yusuf
  - **Dependencies:** 1.1, 1.2
  - **Acceptance Criteria:** Both configs follow the helloworld `AgentConfig` pattern. Fields include name, style, prompt, max_call_duration, max_history_messages, debug_mode.

---

### Phase 2: Backend (Python)

**Goal:** Build the FastAPI backend that proxies Vocal Bridge tokens, serves scenario data, captures transcripts, and triggers coaching evaluation.

**Dependencies:** Phase 1 (agent designs complete), Phase 0 (tooling works)

#### Tasks

- [ ] **2.1 — Implement scenario API endpoint**
  - **Description:** Add `GET /api/scenarios` to `src/backend/main.py` that returns the list of scenarios (from task 1.5) with trainee-visible fields only (id, title, difficulty, description). Do NOT expose persona details or actor strategy.
  - **Owner:** Yusuf
  - **Dependencies:** 1.5
  - **Acceptance Criteria:** Returns JSON array of 3 scenarios. No agent-only fields exposed. CORS enabled (already configured in `main.py`).

- [ ] **2.2 — Implement Vocal Bridge token proxy endpoint**
  - **Description:** Add `POST /api/session` endpoint following the exact pattern from `docs/helloworld/server.py` `create_session()` function. Accepts `{ scenario_id, participant_name }`. Calls Vocal Bridge `POST /api/v1/token` with `X-API-Key` header. Returns `{ livekit_url, token, room_name }`. Must inject scenario context into the session so the Simulation Agent receives the right persona via `session_context` client action.
  - **Owner:** Yusuf
  - **Dependencies:** 0.4 (VB_API_KEY in env), 1.3 (client actions defined)
  - **Acceptance Criteria:** Endpoint returns valid LiveKit token. Frontend can connect to LiveKit room. Simulation Agent receives scenario context. Error handling for missing/invalid API key.

- [ ] **2.3 — Implement transcript capture mechanism**
  - **Description:** Design how the full conversation transcript gets from the LiveKit session to the backend. Two options: (a) Frontend accumulates transcript from LiveKit `send_transcript` events and POSTs it to backend when simulation ends, or (b) Backend listens for transcript events via Vocal Bridge webhook/API. Option (a) is simpler and matches the helloworld `app.js` `appendTranscript` pattern. Create `POST /api/transcript` endpoint that accepts `{ scenario_id, transcript: [{role, text, timestamp}] }`.
  - **Owner:** Yusuf
  - **Dependencies:** 2.2
  - **Acceptance Criteria:** Full conversation transcript (both sides) is captured with speaker labels and timestamps. Transcript is stored in-memory for the session (no database per PRD §7).

- [ ] **2.4 — Implement coaching evaluation endpoint**
  - **Description:** Add `POST /api/coaching` endpoint that takes `{ scenario_id, transcript }`, constructs the Coaching Agent prompt (from task 1.2) with the transcript + manual + rubric, and returns structured evaluation. This could invoke a Vocal Bridge Coaching Agent session OR call an LLM API directly. Decision needed (see §5 Key Decisions). Return format: `{ scores: [{category, score, max, summary, manual_ref}], overall_score, improvement_areas: [{title, detail, manual_ref}], interactive_coaching: string }`.
  - **Owner:** Yusuf
  - **Dependencies:** 1.2 (coaching prompt), 2.3 (transcript available)
  - **Acceptance Criteria:** Returns structured JSON matching PRD §6 format. Every score category cites a manual section. At least 2 improvement areas identified. Response time under 30 seconds.

- [ ] **2.5 — Implement agent setup script**
  - **Description:** Create `src/backend/agents/setup_agents.py` following `docs/helloworld/setup_agent.py` pattern. Uses `vb` CLI to create both agents, configure settings, and register client actions. Should be idempotent (check if agents exist before creating).
  - **Owner:** Yusuf
  - **Dependencies:** 1.1, 1.2, 1.3, 1.4, 1.6
  - **Acceptance Criteria:** Running `python setup_agents.py` creates both agents in Vocal Bridge. `vb agent` shows both agents. Client actions are registered. Script is idempotent.

- [ ] **2.6 — Add vocal-bridge and dependencies to requirements.txt**
  - **Description:** Update `src/backend/requirements.txt` to include `vocal-bridge>=0.7.1`, `python-dotenv`, `requests` (following `docs/helloworld/requirements.txt` pattern), plus any LLM SDK needed for coaching (e.g., `openai` if using OpenAI directly).
  - **Owner:** Yusuf
  - **Dependencies:** None
  - **Acceptance Criteria:** `pip install -r requirements.txt` succeeds. All imports in backend code resolve.

---

### Phase 3: Frontend (TypeScript)

**Goal:** Build the three-screen web UI: scenario picker → live simulation with transcript → coaching results.

**Dependencies:** Phase 2 (backend endpoints exist to call), Phase 1 (data structures defined)

#### Tasks

- [ ] **3.1 — Set up React/TS project structure**
  - **Description:** Initialize a React + TypeScript app in `src/frontend/`. Set up routing for three screens: `/` (scenario picker), `/simulation/:scenarioId` (live voice session), `/results` (coaching results). Configure the Express server (`server.js`) to serve the built React app and proxy API calls to the backend.
  - **Owner:** Eames
  - **Dependencies:** None (can scaffold independently)
  - **Acceptance Criteria:** `npm install && npm run build` succeeds. Three routes render placeholder content. Dev server runs on HTTPS with Aspire-provided certs.

- [ ] **3.2 — Build Scenario Picker screen**
  - **Description:** Create the scenario selection UI. Fetch scenarios from `GET /api/scenarios`. Display 3 cards with difficulty badge (Easy/Medium/Hard), title, and one-line description. Clicking a card navigates to the simulation screen with the scenario ID.
  - **Owner:** Eames + Ariadne (design)
  - **Dependencies:** 2.1 (scenario API), 3.1
  - **Acceptance Criteria:** Displays all 3 scenarios from API. Difficulty badges are color-coded (green/yellow/red). Clicking a card navigates to `/simulation/:id`. Mobile-responsive.

- [ ] **3.3 — Build Simulation View screen (LiveKit integration)**
  - **Description:** Create the live voice simulation screen. Pattern from `docs/helloworld/web_embed/app.js`: (a) POST to `/api/session` with scenario ID to get LiveKit token, (b) connect LiveKit Room, (c) publish microphone, (d) receive agent audio, (e) display real-time transcript from `send_transcript` events, (f) show audio visualizer during active speech, (g) handle `end_simulation` client action to transition to coaching. Include a text fallback input for environments without mic access.
  - **Owner:** Eames
  - **Dependencies:** 2.2 (token endpoint), 3.1
  - **Acceptance Criteria:** LiveKit connection established. Microphone audio sent to agent. Agent audio plays in browser. Transcript updates in real-time. `end_simulation` triggers transition. Audio visualizer shows activity. Text fallback works.

- [ ] **3.4 — Implement transcript accumulation and handoff**
  - **Description:** During the simulation, accumulate the full transcript (both agent and user turns with timestamps). When `end_simulation` fires, POST the transcript to `POST /api/transcript`, then call `POST /api/coaching` with the scenario + transcript. Navigate to the results screen when coaching response arrives.
  - **Owner:** Eames
  - **Dependencies:** 2.3 (transcript endpoint), 2.4 (coaching endpoint), 3.3
  - **Acceptance Criteria:** Complete transcript with speaker labels sent to backend. Coaching evaluation returned. Loading state shown while coaching processes. Results screen renders.

- [ ] **3.5 — Build Coaching Results screen**
  - **Description:** Display the structured coaching evaluation. Show: (a) per-category score cards (score/max, category name, summary, manual section reference), (b) overall score prominently, (c) key improvement areas with actionable recommendations citing manual sections, (d) optional: interactive coaching dialogue text. Design should match the quality of PRD §6 example output. Include a "Try Another Scenario" button to return to the picker.
  - **Owner:** Eames + Ariadne (design)
  - **Dependencies:** 2.4 (coaching response format), 3.4
  - **Acceptance Criteria:** All score categories from PRD §6 displayed. Manual section citations rendered as references (e.g., "§2.1"). Overall score prominent. Improvement areas listed. "Try Another" navigates to picker.

- [ ] **3.6 — Design visual identity and UX flow**
  - **Description:** Design the overall look and feel: color scheme, typography, spacing, animations. Design the three screens and transitions between them. Consider: loading states during token fetch and coaching evaluation, error states, audio permission prompts. Design the transcript display for readability during a live conversation.
  - **Owner:** Ariadne
  - **Dependencies:** 3.1
  - **Acceptance Criteria:** Figma or coded mockups for all 3 screens. Consistent visual language. Loading and error states designed. Transcript is readable at conversation speed. Mobile-responsive layouts.

---

### Phase 4: Integration

**Goal:** Wire everything through the Aspire AppHost. Both agents work. Full flow from scenario selection to coaching results.

**Dependencies:** Phase 2 + Phase 3 substantially complete

#### Tasks

- [ ] **4.1 — Update Aspire AppHost for VoiceCoach**
  - **Description:** Update `src/VoiceProject.AppHost/Program.cs` to pass all required environment variables to the backend: `VB_API_KEY`, `VB_API_URL`, any LLM API keys needed for coaching. Ensure frontend can reach backend via the existing `WithReference(backend)` pattern.
  - **Owner:** Browning
  - **Dependencies:** 2.2, 2.4
  - **Acceptance Criteria:** `aspire run` starts both frontend and backend. Backend has all required env vars. Frontend can call backend APIs. Aspire dashboard shows both resources healthy.

- [ ] **4.2 — Run Vocal Bridge agent setup via Aspire**
  - **Description:** Integrate `setup_agents.py` into the development workflow. Either: (a) add as a pre-start script in Aspire, or (b) create a one-time setup command documented in README. Agents must be created in Vocal Bridge before the app can issue tokens.
  - **Owner:** Browning + Yusuf
  - **Dependencies:** 2.5
  - **Acceptance Criteria:** Developer can go from `git clone` to working app with documented steps. Agent setup is clear and idempotent.

- [ ] **4.3 — End-to-end integration test (manual)**
  - **Description:** Run the full flow: `aspire run` → open frontend → select Scenario 1 (Easy) → start voice simulation → have a conversation → simulation ends → coaching results appear. Verify transcript accuracy, coaching quality, and manual citations.
  - **Owner:** Saito
  - **Dependencies:** 4.1, 4.2
  - **Acceptance Criteria:** Complete flow works without errors. Transcript matches spoken conversation. Coaching cites correct manual sections. Scores are reasonable for the conversation quality.

- [ ] **4.4 — Add OpenTelemetry instrumentation**
  - **Description:** Add tracing to backend endpoints (token proxy, transcript capture, coaching evaluation). Ensure traces flow through to Aspire dashboard and Application Insights. Tag spans with scenario ID for filtering.
  - **Owner:** Browning
  - **Dependencies:** 4.1
  - **Acceptance Criteria:** Traces visible in Aspire dashboard. Each API call creates a span. Coaching evaluation duration tracked. Errors captured in traces.

---

### Phase 5: Testing & Polish

**Goal:** Run all 3 scenarios, validate coaching output quality, fix edge cases, polish UX.

**Dependencies:** Phase 4 complete

#### Tasks

- [ ] **5.1 — Test Scenario 1: Simple Product Inquiry (Easy)**
  - **Description:** Run through Scenario 1 multiple times. Verify: AI customer (Sarah) stays in character, asks about coffee maker, tests §4.1 (clarifying question) and §4.2 (shipping threshold). Coaching correctly identifies whether trainee followed §1.1, §1.3, §4.1, §4.2.
  - **Owner:** Saito
  - **Dependencies:** 4.3
  - **Acceptance Criteria:** Simulation agent plays Sarah persona correctly. Tests at least 2 manual sections. Coaching feedback references correct sections. Run 3 times to check consistency.

- [ ] **5.2 — Test Scenario 2: Multi-Issue Order Problem (Medium)**
  - **Description:** Test with David's two-issue order. Verify: agent reveals issues one at a time, tests §1.2 (active listening), §2.1–§2.3 (returns/exchanges), §4.2 (loyalty). Coaching catches missed procedures.
  - **Owner:** Saito
  - **Dependencies:** 4.3
  - **Acceptance Criteria:** Agent presents vacuum issue first, towel issue second. Tests order verification per §2.1. Coaching evaluates all relevant manual sections. Loyalty points question handled correctly.

- [ ] **5.3 — Test Scenario 3: Angry Customer Escalation (Hard)**
  - **Description:** Test with Karen's escalation scenario. Verify: agent pushes for refund, mentions manager once (testing §3.3), escalates emotionally. Coaching evaluates HEAT framework (§3.1), goodwill gesture (§3.2), escalation handling (§3.3), prohibited actions (§5.1).
  - **Owner:** Saito
  - **Dependencies:** 4.3
  - **Acceptance Criteria:** Agent creates realistic escalation pressure. Tests §3.1, §3.2, §3.3, §5.1. Coaching correctly flags any premature manager transfer or prohibited refund promise. De-escalation scoring matches PRD §6 example.

- [ ] **5.4 — Prompt tuning based on test results**
  - **Description:** Based on testing results from 5.1–5.3, refine both agent prompts. Simulation agent: tune actor strategy depth, persona consistency, conversation pacing. Coaching agent: tune scoring calibration, feedback specificity, manual citation accuracy.
  - **Owner:** Cobb + Yusuf
  - **Dependencies:** 5.1, 5.2, 5.3
  - **Acceptance Criteria:** Simulation agent consistently tests the intended manual sections. Coaching scores correlate with actual trainee performance. Feedback is specific and actionable, not generic.

- [ ] **5.5 — UX polish and error handling**
  - **Description:** Polish transitions between screens. Add: microphone permission prompt with clear instructions, loading spinners during token fetch and coaching eval, error messages for network/API failures, graceful handling of mid-conversation disconnects. Ensure the coaching results screen is scannable and professional.
  - **Owner:** Eames + Ariadne
  - **Dependencies:** 5.1, 5.2, 5.3
  - **Acceptance Criteria:** No blank screens or unhandled errors. Microphone permission flow is clear. Loading states show progress. Error messages are user-friendly. Coaching results look polished.

- [ ] **5.6 — Write developer README**
  - **Description:** Write `README.md` at project root with: prerequisites, setup steps (API keys, agent creation, `aspire run`), architecture overview, scenario descriptions, and contribution guidelines. Reference the helloworld README as a template for the Vocal Bridge setup section.
  - **Owner:** Arthur
  - **Dependencies:** 4.2
  - **Acceptance Criteria:** A new developer can go from `git clone` to running app by following the README. All prerequisites listed. Setup steps verified on a clean environment.

---

## 4. Detailed Work Item Summary

### Assignment Matrix

| Phase | # Items | Cobb | Arthur | Ariadne | Eames | Yusuf | Saito | Browning |
|-------|---------|------|--------|---------|-------|-------|-------|----------|
| 0 — Setup | 4 | | | | | | | 4 |
| 1 — Agent Design | 6 | 4 | | | | 2 | | |
| 2 — Backend | 6 | | | | | 6 | | |
| 3 — Frontend | 6 | | | 2 | 5 | | | |
| 4 — Integration | 4 | | | | | 1 | 1 | 3 |
| 5 — Polish | 6 | 1 | 1 | 1 | 1 | 1 | 3 | |
| **Total** | **32** | **5** | **1** | **3** | **6** | **10** | **4** | **7** |

*Note: Some tasks have shared ownership (counted for each owner). Scribe and Ralph are operational — not assigned product work.*

### Dependency Chain (Critical Path)

```
0.1 → 0.2 → 0.3 → 0.4
                  ↓
            1.1 → 1.2 → 1.4
             ↓         ↓
            1.3   1.5  1.6
             ↓     ↓    ↓
            2.2 → 2.3 → 2.4 → 4.3 → 5.1/5.2/5.3 → 5.4
             ↑                   ↑
            2.1                 4.1 → 4.4
             ↑                   ↑
            1.5                 2.5 → 4.2
                                      ↑
                               3.1 → 3.2 → 3.3 → 3.4 → 3.5
                                ↓
                               3.6
```

**Critical path:** 0.1 → 0.3 → 1.1 → 1.2 → 2.4 → 4.3 → 5.1 → 5.4

---

## 5. Key Technical Decisions Needed

### Decision 1: One Vocal Bridge Agent or Two?

**Options:**
- **(A) Two separate Vocal Bridge agents** — One for simulation (voice-interactive), one for coaching (could be voice or text-only). Pro: Clean separation, independent tuning. Con: Two agents to manage, two token calls.
- **(B) One Vocal Bridge agent for simulation + direct LLM call for coaching** — Simulation uses Vocal Bridge (voice). Coaching is a plain API call to OpenAI/Anthropic with the transcript. Pro: Coaching doesn't need voice; simpler. Con: Coaching can't be voice-interactive later.
- **(C) One Vocal Bridge agent that does both** — Single agent handles simulation, then transitions to coaching mode. Pro: Single session. Con: Complex prompt management, can't tune independently.

**Recommendation:** **(B)** — Vocal Bridge for simulation (it needs real-time voice), direct LLM call for coaching (it's a text-in/text-out evaluation). This is the simplest path to MVP. We can upgrade coaching to voice later if users want to discuss feedback verbally.

### Decision 2: How Does the Transcript Get from Simulation to Coaching?

**Options:**
- **(A) Frontend accumulates and POSTs** — Frontend captures transcript from LiveKit events (like helloworld `app.js` does), POSTs to backend when simulation ends.
- **(B) Backend captures via webhook** — Vocal Bridge sends transcript events to a webhook on the backend.
- **(C) Backend polls Vocal Bridge API** — After session ends, backend fetches transcript from Vocal Bridge.

**Recommendation:** **(A)** — Frontend accumulation. It's the pattern already demonstrated in `app.js` `appendTranscript()`. Simple, no webhook infrastructure needed for MVP.

### Decision 3: How to Handle Scenario Context Injection?

**Options:**
- **(A) `session_context` client action** — Frontend sends scenario persona details via the `session_context` action at session start (pattern from helloworld `client_actions.json`).
- **(B) Prompt templating** — Create separate Vocal Bridge agents per scenario, each with a hardcoded prompt.
- **(C) Dynamic prompt via API** — Update agent prompt before each session via `vb` CLI or API.

**Recommendation:** **(A)** — Use `session_context`. It's the established Vocal Bridge pattern. The simulation agent's base prompt includes the manual + catalog + generic actor instructions, and the `session_context` injects the specific persona (Sarah/David/Karen) and scenario rules at session start.

### Decision 4: Coaching Agent — Voice-Interactive or Text-Only?

**Options:**
- **(A) Text-only evaluation** — Backend makes an LLM API call, returns structured JSON immediately.
- **(B) Voice-interactive coaching** — Trainee can ask follow-up questions about their performance in a voice conversation with the coach.

**Recommendation:** **(A) for MVP.** Text-only is faster to build and test. The PRD shows coaching as a structured output (scores + feedback), not a conversation. We can add voice coaching in a future iteration if user testing indicates demand.

### Decision 5: LLM Provider for Coaching Evaluation

**Options:** OpenAI (GPT-4o), Anthropic (Claude), Azure OpenAI

**Recommendation:** Defer to Yusuf. The coaching prompt needs structured JSON output, manual citation accuracy, and consistent scoring. Test with the cheapest option that produces reliable results.

---

## 6. Risk Register

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| 1 | **Voice naturalness** — AI customer sounds robotic or predictable, trainees disengage | High | Medium | Vocal Bridge handles TTS/voice quality. Tune prompts for conversational cadence. Test with real users early in Phase 5. This is *exactly* what the MVP acceptance test is for. |
| 2 | **Manual coverage gaps** — Abridged manual (§1–§5) doesn't cover edge cases testers attempt | Medium | Medium | Manual covers the 3 scenarios fully. If gaps appear during testing, add sections. Log uncovered situations for production manual expansion. |
| 3 | **Prompt quality / actor depth** — Simulation agent doesn't probe deeply enough, coaching loses value | High | Medium | PRD §5 defines specific actor strategies per scenario. Iterate prompts in Phase 5.4. Test the hard scenario (Karen) extensively — it has the most nuanced testing requirements. |
| 4 | **Vocal Bridge API availability / reliability** — Third-party dependency for voice infrastructure | High | Low | Vocal Bridge is the established pattern. Helloworld proves it works. No fallback for MVP — if VB is down, the app is down. Acceptable for user acceptance test scope. |
| 5 | **Transcript accuracy** — LiveKit `send_transcript` events miss or garble words | Medium | Medium | Display transcript in real-time so trainee can verify during simulation. Coaching agent should be instructed to evaluate based on available transcript (not penalize for transcription errors). |
| 6 | **Coaching scoring inconsistency** — Same conversation gets different scores on repeat evaluation | Medium | Medium | Use structured output format (JSON mode) with explicit rubric. Test scoring consistency in Phase 5. Consider temperature=0 for deterministic results. |
| 7 | **Context window limits** — Long conversations (Scenario 3 can go 5+ minutes) may exceed LLM token limits | Low | Low | 10-minute cap on simulation (Vocal Bridge `max_call_duration`). At ~150 words/minute, 10 min ≈ 1,500 words ≈ 2,000 tokens. Well within limits for any modern LLM. |
| 8 | **Browser microphone permissions** — Users confused by mic access prompts, can't start simulation | Medium | Medium | Clear UX guidance before mic prompt (task 5.5). Text input fallback available. Test across Chrome, Firefox, Edge. |

---

## 7. Reference Materials

| Document | Path | Purpose |
|---|---|---|
| MVP Product Brief (PRD) | `docs/voiceagent-mvp-brief.md` | Complete product requirements, scenarios, manual, catalog |
| Helloworld Reference | `docs/helloworld/` | Vocal Bridge integration patterns — config, setup, server, web embed |
| Agent Config Pattern | `docs/helloworld/config.py` | `AgentConfig` dataclass structure |
| Agent Setup Pattern | `docs/helloworld/setup_agent.py` | `vb` CLI usage for agent creation |
| Client Actions Pattern | `docs/helloworld/client_actions.json` | `send_document`, `end_conversation`, `session_context` |
| Token Proxy Pattern | `docs/helloworld/server.py` | `POST /api/v1/token` with `X-API-Key` header |
| Web Client Pattern | `docs/helloworld/web_embed/app.js` | LiveKit Room connection, transcript capture, client action handling |
| Prompt Pattern | `docs/helloworld/vb-agent-prompt.md` | System prompt structure and client action instructions |
| Aspire AppHost | `src/VoiceProject.AppHost/Program.cs` | Current orchestration config (Python backend + npm frontend) |
| Current Backend | `src/backend/main.py` | FastAPI skeleton with CORS |
| Current Frontend | `src/frontend/` | Express + static HTML (to become React/TS) |

---

*This plan is the source of truth for VoiceCoach MVP work decomposition. Each checkbox task above should become a GitHub issue. Phase ordering is sequential but tasks within a phase can be parallelized per the dependency chain in §4.*
