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
