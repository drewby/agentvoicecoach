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
