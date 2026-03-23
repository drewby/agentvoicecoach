---
name: opentelemetry-aspire
description: 'OpenTelemetry skill covering trace span creation, context propagation, and exporting telemetry to the .NET Aspire dashboard — focused on TypeScript and Python. Use when the user asks to instrument a service with OpenTelemetry, create manual spans, add attributes or events to traces, configure OTLP exporters, connect telemetry to the Aspire dashboard, set up auto-instrumentation, propagate trace context across services, or troubleshoot missing or broken traces. Also trigger when the user mentions tracing, spans, OTLP, or observability in the context of a distributed app.'
---

# OpenTelemetry → Aspire — Tracing for TypeScript & Python

OpenTelemetry (OTel) is the **vendor-neutral observability standard** for distributed tracing, metrics, and logs. This skill focuses on the most common need: **creating trace spans in TypeScript and Python services and exporting them to the .NET Aspire dashboard**.

> **Mental model:** A *trace* is a tree of *spans*. Each span records one unit of work (an HTTP request, a DB query, a function call). The Aspire dashboard collects these spans via OTLP and renders them as a waterfall timeline.

Detailed reference material lives in the `references/` folder — load on demand.

---

## References

| Reference | When to load |
|---|---|
| [TypeScript Instrumentation](references/typescript.md) | Full setup, SDK config, manual spans, auto-instrumentation for Node.js/Express/Fastify |
| [Python Instrumentation](references/python.md) | Full setup, SDK config, manual spans, auto-instrumentation for Flask/FastAPI/Django |
| [Aspire Integration](references/aspire-integration.md) | Wiring OTel exporters to Aspire, env vars, dashboard features, Docker Compose fallback |
| [Context Propagation](references/context-propagation.md) | W3C Trace Context, cross-service headers, baggage, manual propagation patterns |
| [Troubleshooting](references/troubleshooting.md) | Missing spans, broken traces, exporter errors, diagnostic logging |

---

## 1. How Aspire Receives Telemetry

The Aspire dashboard runs an **OTLP (OpenTelemetry Protocol) collector endpoint** that accepts gRPC and HTTP/protobuf.

When you launch services via `aspire run`, the AppHost automatically injects these environment variables into every resource:

| Variable | Typical Value | Purpose |
|---|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` (gRPC) or `http://localhost:4318` (HTTP) | Where to send telemetry |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `grpc` or `http/protobuf` | Transport protocol |
| `OTEL_RESOURCE_ATTRIBUTES` | `service.name=my-service` | Resource identity |
| `OTEL_SERVICE_NAME` | `my-service` | Shorthand for service name |
| `OTEL_EXPORTER_OTLP_HEADERS` | `x-otlp-api-key=<token>` | Dashboard auth token |

> **Key insight:** If your OTel SDK is configured to read standard env vars (which is the default), Aspire integration is essentially zero-config. Just set up the SDK and the env vars do the rest.

---

## 2. Quick Start — TypeScript (Node.js)

### Install

```bash
npm install @opentelemetry/sdk-node \
  @opentelemetry/api \
  @opentelemetry/exporter-trace-otlp-grpc \
  @opentelemetry/sdk-trace-node \
  @opentelemetry/resources \
  @opentelemetry/semantic-conventions
```

### Minimal tracing setup (`tracing.ts`)

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-grpc";
import { Resource } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";

const sdk = new NodeSDK({
  resource: new Resource({
    [ATTR_SERVICE_NAME]: process.env.OTEL_SERVICE_NAME ?? "my-ts-service",
  }),
  traceExporter: new OTLPTraceExporter({
    // Reads OTEL_EXPORTER_OTLP_ENDPOINT automatically if not set here
  }),
});

sdk.start();

// Graceful shutdown
process.on("SIGTERM", () => sdk.shutdown());
```

> **Import this file first** — before any other application code. Use `--require` / `--import` or import at the top of your entry point.

### Creating manual spans

```typescript
import { trace, SpanStatusCode } from "@opentelemetry/api";

const tracer = trace.getTracer("my-service", "1.0.0");

async function processOrder(orderId: string) {
  return tracer.startActiveSpan("process-order", async (span) => {
    try {
      span.setAttribute("order.id", orderId);

      // Child span — automatically nested under "process-order"
      await tracer.startActiveSpan("validate-payment", async (child) => {
        span.addEvent("payment_validated", { "payment.method": "card" });
        child.end();
      });

      span.setStatus({ code: SpanStatusCode.OK });
    } catch (err) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
      span.recordException(err as Error);
      throw err;
    } finally {
      span.end();
    }
  });
}
```

For full TypeScript details (auto-instrumentation, Express/Fastify, ESM vs CJS), see [TypeScript Instrumentation](references/typescript.md).

---

## 3. Quick Start — Python

### Install

```bash
pip install opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp-proto-grpc
```

### Minimal tracing setup (`tracing.py`)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
import os

resource = Resource.create({
    SERVICE_NAME: os.environ.get("OTEL_SERVICE_NAME", "my-py-service"),
})

provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter()  # Reads OTEL_EXPORTER_OTLP_ENDPOINT from env
    )
)
trace.set_tracer_provider(provider)
```

> **Import this module before your app starts** — at the top of your entry point or via `sitecustomize.py`.

### Creating manual spans

```python
from opentelemetry import trace
from opentelemetry.trace import StatusCode

tracer = trace.get_tracer("my-service", "1.0.0")

def process_order(order_id: str):
    with tracer.start_as_current_span("process-order") as span:
        span.set_attribute("order.id", order_id)

        # Child span — automatically nested
        with tracer.start_as_current_span("validate-payment") as child:
            span.add_event("payment_validated", {"payment.method": "card"})

        span.set_status(StatusCode.OK)
```

### Error recording

```python
try:
    with tracer.start_as_current_span("risky-operation") as span:
        do_something()
except Exception as e:
    span.set_status(StatusCode.ERROR, str(e))
    span.record_exception(e)
    raise
```

For full Python details (auto-instrumentation, Flask/FastAPI/Django, programmatic vs env config), see [Python Instrumentation](references/python.md).

---

## 4. Core Concepts (Summary)

| Concept | Key point |
|---|---|
| **Trace** | A tree of spans sharing one `trace_id`. Represents an end-to-end request. |
| **Span** | One unit of work. Has a name, start/end time, attributes, events, status, and parent. |
| **Tracer** | Factory for spans. Create one per module/component: `trace.getTracer("name")`. |
| **TracerProvider** | Holds configuration (exporters, processors, resource). Set once at startup. |
| **Resource** | Metadata about the service (name, version, environment). Attached to all spans. |
| **SpanProcessor** | Pipeline stage between span creation and export. `BatchSpanProcessor` is the default for production. |
| **Exporter** | Sends spans to a backend. `OTLPTraceExporter` for Aspire / any OTLP collector. |
| **Context propagation** | Carries the active span across async boundaries and HTTP calls. Uses W3C `traceparent` header. |
| **Semantic conventions** | Standardized attribute names (e.g., `http.request.method`, `db.system`). Use them for dashboard compatibility. |
| **Auto-instrumentation** | Libraries that automatically create spans for HTTP, DB, messaging, etc. Zero code changes. |

---

## 5. Aspire AppHost Wiring

When adding a non-.NET service to the Aspire AppHost, the OTel env vars are injected automatically:

```csharp
// AppHost Program.cs
var api = builder.AddPythonApp("ml-service", "../ml-service", "main.py")
    .WithHttpEndpoint(targetPort: 8000)
    .WithOtlpExporter();   // Ensures OTEL_* env vars are set

var web = builder.AddNpmApp("frontend", "../frontend")
    .WithHttpEndpoint(targetPort: 3000)
    .WithOtlpExporter();
```

> `.WithOtlpExporter()` is often implicit — Aspire injects the env vars for all resources by default in most templates. Check your generated `AppHost` if spans aren't appearing.

For standalone use (no Aspire AppHost), see [Aspire Integration](references/aspire-integration.md) for running the dashboard container directly.

---

## 6. Common Patterns

### Adding tracing to an existing service

1. Install the OTel SDK + OTLP exporter for your language
2. Create a tracing setup file (see Quick Starts above)
3. Import it **before** any application code
4. Create a `tracer` in each module that needs manual spans
5. Wrap key operations in `startActiveSpan` / `start_as_current_span`
6. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to point at Aspire (or any collector)
7. Run and check the Aspire dashboard traces view

### Adding custom attributes to spans

Use **semantic conventions** where they exist, custom names where they don't:

```typescript
// TypeScript
span.setAttribute("http.request.method", "POST");  // semantic convention
span.setAttribute("order.total_cents", 4999);       // custom domain attr
```

```python
# Python
span.set_attribute("http.request.method", "POST")
span.set_attribute("order.total_cents", 4999)
```

### Linking traces across services

When Service A calls Service B over HTTP, the trace context must propagate via headers. Auto-instrumentation handles this for most HTTP libraries. For manual propagation, see [Context Propagation](references/context-propagation.md).

---

## 7. Key URLs

| Resource | URL |
|---|---|
| **OTel JS SDK** | https://github.com/open-telemetry/opentelemetry-js |
| **OTel Python SDK** | https://github.com/open-telemetry/opentelemetry-python |
| **OTel JS API docs** | https://open-telemetry.github.io/opentelemetry-js/ |
| **OTel Python API docs** | https://opentelemetry-python.readthedocs.io/ |
| **Semantic Conventions** | https://opentelemetry.io/docs/specs/semconv/ |
| **OTLP Spec** | https://opentelemetry.io/docs/specs/otlp/ |
| **Aspire Dashboard image** | `mcr.microsoft.com/dotnet/aspire-dashboard` |
| **Aspire docs** | https://aspire.dev |