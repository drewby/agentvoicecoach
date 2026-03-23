# Squad Decisions

## Active Decisions

No decisions recorded yet.

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


