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
