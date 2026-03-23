# History

## Core Context
Project: A Python backend and TypeScript frontend for a 2-hour hackathon, aiming for a high-quality MVP. Awaiting the product challenge. User: Drew Robbins.
Tech: Python, TypeScript, Aspire toolkit, OpenTelemetry, Azure App Insights, Azure CI/CD.

## Learnings

## 20260323T041749Z
Task: Setup project structure, Aspire, Github Repo (sync)
## Learnings
- Project structured with Python backend and React/TS frontend under src/.
- GitHub Action created for deploy.

## Learnings
- Project structured with Python backend and React/TS frontend under src/.
- GitHub Action created for deploy.


## Learnings
- **Architecture**: Decided to use .NET Aspire (`dotnet new aspire-apphost`) as the primary orchestrator for managing the Python backend and TS/React frontend.
- **Key File Paths**: The orchestration project is in `src/VoiceProject.AppHost`, with configuration in `Program.cs`. The Python backend is at `src/backend` and the TS/React frontend at `src/frontend`.
- **User Preferences**: Drew prefers using `aspire-apphost` for a unified development experience and deployment strategy across multiple varied tech stacks.
- 2026-03-23T05:02:33Z: Added Aspire app host orchestration for polyglot setup.
