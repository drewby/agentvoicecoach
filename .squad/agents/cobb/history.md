# History

## Core Context
Project: A Python backend and TypeScript frontend for a 2-hour hackathon, aiming for a high-quality MVP. Awaiting the product challenge. User: Drew Robbins.
Tech: Python, TypeScript, Aspire toolkit, OpenTelemetry, Azure App Insights, Azure CI/CD.

## Learnings

### 2026-03-23: VoiceCoach Plan Created
- Created comprehensive plan at `docs/voicecoach-plan.md` — 6 phases, 32 work items, full dependency chain
- Architecture maps directly to `docs/helloworld/` Vocal Bridge patterns: config.py → agent configs, setup_agent.py → setup_agents.py, server.py → FastAPI endpoints, web_embed/ → React frontend
- Recommended Option B for coaching: Vocal Bridge for simulation (needs voice), plain LLM call for coaching (text-in/text-out). Simplest MVP path.
- Recommended frontend transcript accumulation (Option A) for sim→coaching handoff — matches existing `app.js` `appendTranscript` pattern
- Recommended `session_context` client action for scenario injection — established Vocal Bridge pattern
- Key file paths: PRD at `docs/voiceagent-mvp-brief.md`, plan at `docs/voicecoach-plan.md`, AppHost at `src/VoiceProject.AppHost/Program.cs`
- 5 key technical decisions flagged for team discussion
- Critical path: Phase 0 setup → Phase 1 agent prompts → Phase 2 backend coaching endpoint → Phase 4 integration → Phase 5 scenario testing
- Yusuf carries the heaviest load (10 items, all backend). Eames is second (6 items, all frontend). Browning owns Phase 0 + integration infra.

### 2026-03-23: Phase 1 — Agent Design Artifacts Created
- Created all 6 agent design files under `src/backend/agents/`:
  - `simulation_prompt.md` — Full system prompt for AI customer, includes complete employee manual (§1–§5), full product catalog (8 SKUs), session_context/end_simulation client action instructions, voice interaction guidelines
  - `coaching_prompt.md` — Full system prompt for coaching evaluator, includes complete employee manual, 8-category scoring rubric (1-10 each with criteria tied to manual sections), JSON output format matching PRD §6 example, send_evaluation/send_document/end_conversation flow
  - `scenarios.json` — All 3 scenarios (Sarah/Easy, David/Medium, Karen/Hard) with full persona, goal, behavior, actor_strategy, manual_sections_tested, opening_line, products_involved
  - `client_actions_sim.json` — end_simulation + session_context
  - `client_actions_coach.json` — send_evaluation + send_document + end_conversation + session_context
  - `config.py` — SimulationAgentConfig + CoachingAgentConfig dataclasses with path helpers, follows helloworld/config.py pattern
- Decision: Employee manual copied VERBATIM into both prompts (not referenced by path) — both agents need it in their context window
- Decision: Coaching agent receives transcript via session_context client action (text-based, not voice)
- Decision: N/A categories in scoring rubric still included in JSON output (score=null, applicable=false) for frontend consistency
- Key files: all under `src/backend/agents/`
