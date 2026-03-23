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
