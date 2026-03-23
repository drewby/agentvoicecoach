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
