// Browser OpenTelemetry SDK — bundled via esbuild into public/otel-bundle.js
// Sends traces + log records to the Aspire dashboard OTLP HTTP endpoint.
// API: window.__otel = { ready, startPhase, tracedFetch }
// See: docs/telemetry-architecture.md (Section 4)
import { WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { OTLPLogExporter } from "@opentelemetry/exporter-logs-otlp-http";
import { LoggerProvider, SimpleLogRecordProcessor } from "@opentelemetry/sdk-logs";
import { Resource } from "@opentelemetry/resources";
import { W3CTraceContextPropagator } from "@opentelemetry/core";
import { context, trace, propagation } from "@opentelemetry/api";
import { logs, SeverityNumber } from "@opentelemetry/api-logs";

const resource = new Resource({ "service.name": "voicecoach-browser" });

function parseHeaders(raw) {
  const result = {};
  for (const pair of raw.split(",")) {
    const idx = pair.indexOf("=");
    if (idx > 0) result[pair.slice(0, idx).trim()] = pair.slice(idx + 1).trim();
  }
  return result;
}

let tracer;
let logger;

const ready = fetch("/otel-config")
  .then((r) => r.json())
  .then((cfg) => {
    const exporterOpts = {};
    const logExporterOpts = {};
    if (cfg.endpoint) {
      exporterOpts.url = cfg.endpoint + "/v1/traces";
      logExporterOpts.url = cfg.endpoint + "/v1/logs";
    }
    if (cfg.headers) {
      exporterOpts.headers = parseHeaders(cfg.headers);
      logExporterOpts.headers = parseHeaders(cfg.headers);
    }

    const provider = new WebTracerProvider({ resource });
    provider.addSpanProcessor(new BatchSpanProcessor(new OTLPTraceExporter(exporterOpts)));
    provider.register({ propagator: new W3CTraceContextPropagator() });
    tracer = trace.getTracer("voicecoach-browser");

    const logExporter = new OTLPLogExporter(logExporterOpts);
    const logProvider = new LoggerProvider({
      resource,
      processors: [new SimpleLogRecordProcessor(logExporter)],
    });
    logs.setGlobalLoggerProvider(logProvider);
    logger = logs.getLogger("voicecoach-browser");
    console.log("[OTel] Trace + Log providers initialized");
  })
  .catch((err) => {
    console.warn("[OTel] Could not load OTLP config — telemetry disabled", err);
    tracer = trace.getTracer("voicecoach-browser");
    logger = null;
  });

// ---------------------------------------------------------------------------
// Emit a log record correlated to a specific span via context.
// This is the correct pattern: trace.setSpan() creates a context carrying the
// span, and passing that context to logger.emit() links the log record to the
// span's trace_id + span_id.
// ---------------------------------------------------------------------------
function emitLogRecord(targetSpan, eventName, attributes) {
  if (!logger) {
    console.warn("[OTel] emitLogRecord skipped — logger is null:", eventName);
    return;
  }
  try {
    const spanContext = trace.setSpan(context.active(), targetSpan);
    const sc = targetSpan.spanContext ? targetSpan.spanContext() : null;
    console.log("[OTel] emitLogRecord:", eventName, "traceId:", sc?.traceId, "spanId:", sc?.spanId);
    logger.emit({
      severityNumber: SeverityNumber.INFO,
      severityText: "INFO",
      body: eventName,
      attributes: { "event.name": eventName, ...attributes },
      context: spanContext,
    });
  } catch (err) {
    console.error("[OTel] emitLogRecord error:", eventName, err);
  }
}

// ---------------------------------------------------------------------------
// startPhase(sessionId, phase, attributes) → PhaseContext
// Creates a root span for a session phase and returns a context object.
// ---------------------------------------------------------------------------
function startPhase(sessionId, phase, attributes) {
  const rootSpan = tracer.startSpan(phase, {
    attributes: { "session.id": sessionId, "session.phase": phase, ...attributes },
  });
  const ctx = trace.setSpan(context.active(), rootSpan);

  return {
    rootSpan,
    ctx,

    createChildSpan(name, childAttributes) {
      const span = tracer.startSpan(name, { attributes: childAttributes }, ctx);
      return {
        span,
        addEvent(eventName, eventAttrs) {
          emitLogRecord(span, eventName, eventAttrs);
        },
        setAttribute(key, value) {
          span.setAttribute(key, value);
        },
        end() {
          span.end();
        },
      };
    },

    addEvent(eventName, eventAttributes) {
      emitLogRecord(rootSpan, eventName, eventAttributes);
    },

    end() {
      rootSpan.end();
    },
  };
}

// ---------------------------------------------------------------------------
// tracedFetch(url, options, phaseContext) → Promise<Response>
// Creates a child span for the fetch, injects traceparent, records status.
// ---------------------------------------------------------------------------
function tracedFetch(url, options, phaseContext) {
  const parentCtx = phaseContext ? phaseContext.ctx : context.active();
  const span = tracer.startSpan(
    "fetch " + url,
    { attributes: { "http.method": (options && options.method) || "GET", "http.url": url } },
    parentCtx
  );

  const spanCtx = trace.setSpan(context.active(), span);
  const headers = Object.assign({}, options && options.headers);
  propagation.inject(spanCtx, headers);

  return fetch(url, Object.assign({}, options, { headers }))
    .then(function (resp) {
      span.setAttribute("http.status_code", resp.status);
      span.end();
      return resp;
    })
    .catch(function (err) {
      span.setStatus({ code: 2, message: err.message });
      span.end();
      throw err;
    });
}

// ---------------------------------------------------------------------------
// Expose to window for use by index.html
// ---------------------------------------------------------------------------
window.__otel = { ready, startPhase, tracedFetch };
