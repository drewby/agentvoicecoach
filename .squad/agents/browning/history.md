# History

## Core Context
Project: A Python backend and TypeScript frontend for a 2-hour hackathon, aiming for a high-quality MVP. Awaiting the product challenge. User: Drew Robbins.
Tech: Python, TypeScript, Aspire toolkit, OpenTelemetry, Azure App Insights, Azure CI/CD.

## Learnings

## 20260323T041749Z
Task: Scaffold Azure Bicep and GH Actions (sync)
Added dev-certs-strategy
### Dev Certificates Integration
- Added automated local HTTPS dev certificates deployment to .devcontainer/devcontainer.json.
- Documented how polyglot frontend (Vite/React) and backend (Python) use these certificates from local `tmp/` directory.
### Dev Certificates Integration
- Added automated local HTTPS dev certificates deployment to .devcontainer/devcontainer.json.
- Documented how polyglot frontend (Vite/React) and backend (Python) use these certificates from local `tmp/` directory.

## Learnings
- The dev container image mcr.microsoft.com/devcontainers/dotnet:10.0 does not include python3-venv by default. This needs to be explicitly installed using apt-get in onCreateCommand for polyglot applications to ensure Aspire Python backends work seamlessly without venv missing errors.
- 2026-03-23T05:22:02Z: Fixed python3-venv dependency in dev container.

## 20260323-phase0-tooling
- Installed vocal-bridge 0.14.0 into backend venv (.venv at project root). `vb --version` confirmed working.
- Added vocal-bridge>=0.7.1, python-dotenv>=1.0.0, requests>=2.31.0 to src/backend/requirements.txt.
- Updated Program.cs to pass VB_API_KEY env var to backend via builder.Configuration (not hardcoded).
- Created .env.example at project root with VB_API_KEY placeholder.
