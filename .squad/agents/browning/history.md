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
- Aspire SDK 13.2.0 dashboard only exposes OTLP gRPC by default. To enable OTLP/HTTP (needed for browser telemetry), set `ASPIRE_DASHBOARD_OTLP_HTTP_ENDPOINT_URL` in launchSettings.json. CORS is auto-configured when using AppHost. The HTTP endpoint must be on a separate port from gRPC.
- Aspire auto-injects `OTEL_EXPORTER_OTLP_ENDPOINT` (gRPC) and `OTEL_EXPORTER_OTLP_PROTOCOL=grpc` into all resources. For resources that need OTLP/HTTP, inject a custom env var (e.g., `OTEL_EXPORTER_OTLP_HTTP_ENDPOINT`) by reading `ASPIRE_DASHBOARD_OTLP_HTTP_ENDPOINT_URL` from the AppHost environment.
- The dev container image mcr.microsoft.com/devcontainers/dotnet:10.0 does not include python3-venv by default. This needs to be explicitly installed using apt-get in onCreateCommand for polyglot applications to ensure Aspire Python backends work seamlessly without venv missing errors.
- 2026-03-23T05:22:02Z: Fixed python3-venv dependency in dev container.

## 20260323-phase0-tooling
- Installed vocal-bridge 0.14.0 into backend venv (.venv at project root). `vb --version` confirmed working.
- Added vocal-bridge>=0.7.1, python-dotenv>=1.0.0, requests>=2.31.0 to src/backend/requirements.txt.
- Updated Program.cs to pass VB_API_KEY env var to backend via builder.Configuration (not hardcoded).
- Created .env.example at project root with VB_API_KEY placeholder.

📌 Team update (2026-03-26): Telemetry architecture redesigned — browser /v1/logs confirmed not working (your finding), all browser telemetry moves to span events via /v1/traces. No infra changes needed. See docs/telemetry-architecture.md. — decided by Arthur (synthesizing Yusuf, Eames, Browning)

## 20260325-otel-infra-verification
Task: Verify Aspire AppHost is ready to receive OpenTelemetry traces from the Python backend.

### Findings — No AppHost Changes Needed
- **Aspire SDK 13.1.3 auto-injects all OTEL env vars** into both backend and frontend resources. Confirmed via `list_resources`: `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`, `OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_EXPORTER_OTLP_CERTIFICATE`, `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_SERVICE_NAME`, `OTEL_TRACES_EXPORTER`, `OTEL_TRACES_SAMPLER`, `OTEL_LOGS_EXPORTER`, `OTEL_METRICS_EXPORTER`, plus Python-specific `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED`.
- **Structured logs already flowing**: Backend's `_setup_otel()` successfully connects via OTLP gRPC and all Python logs appear on the Aspire dashboard with source attributes (`code.file.path`, `code.function.name`, `code.line.number`).
- **Traces not yet flowing** (0 traces) — expected because backend only has LoggerProvider, no TracerProvider. Once Yusuf adds trace instrumentation (TracerProvider + BatchSpanProcessor + OTLPSpanExporter), traces will appear automatically since the OTLP endpoint/protocol env vars are already injected.
- **No `WithOtlpExporter()` needed** on the builder — that's for .NET service projects with Aspire service defaults. Python/Node resources receive OTLP config via standard OTel env vars.
- **`Aspire.Hosting.NodeJs` 9.5.2 is the latest available** per `list_integrations`. No newer version exists — not a version mismatch.
- **Frontend Node.js**: OTEL env vars are injected (verified). No OTel SDK installed yet — future enhancement. Console logs sufficient for now.
- **Protocol**: Backend defaults to gRPC when `OTEL_EXPORTER_OTLP_PROTOCOL` doesn't contain "http". Aspire sets this var automatically. The existing code handles both gRPC and HTTP/protobuf correctly.
