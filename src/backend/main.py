import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Logging + OpenTelemetry
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicecoach")

logger.info("OTEL_EXPORTER_OTLP_ENDPOINT = %s", os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "(not set)"))
logger.info("OTEL_EXPORTER_OTLP_HTTP_ENDPOINT = %s", os.environ.get("OTEL_EXPORTER_OTLP_HTTP_ENDPOINT", "(not set)"))
logger.info("OTEL_EXPORTER_OTLP_HEADERS = %s", "(set)" if os.environ.get("OTEL_EXPORTER_OTLP_HEADERS") else "(not set)")

from opentelemetry import trace
from opentelemetry.trace import StatusCode


def _setup_otel() -> None:
    """Wire Python logging and tracing into OpenTelemetry so they appear in Aspire."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    try:
        from opentelemetry.sdk.resources import Resource

        protocol = os.environ.get("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")
        resource = Resource.create()

        # --- Logging ---
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

        if "http" in protocol:
            from opentelemetry.exporter.otlp.proto.http._log_exporter import (
                OTLPLogExporter,
            )
        else:
            from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
                OTLPLogExporter,
            )

        log_provider = LoggerProvider(resource=resource)
        log_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
        set_logger_provider(log_provider)
        logging.getLogger().addHandler(LoggingHandler(logger_provider=log_provider))
        logger.info("OpenTelemetry logging configured")

        # --- Tracing ---
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        if "http" in protocol:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
        else:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)
        logger.info("OpenTelemetry tracing configured")

    except Exception as exc:
        logger.warning("OpenTelemetry setup failed: %s", exc)


_setup_otel()
tracer = trace.get_tracer("voicecoach")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
AGENTS_DIR = Path(__file__).resolve().parent / "agents"
SCENARIOS_FILE = AGENTS_DIR / "scenarios.json"
SIMULATION_PROMPT_FILE = AGENTS_DIR / "simulation_prompt.md"
COACHING_PROMPT_FILE = AGENTS_DIR / "coaching_prompt.md"
FEEDBACK_PROMPT_FILE = AGENTS_DIR / "feedback_prompt.md"
EMPLOYEE_MANUAL_FILE = AGENTS_DIR / "employee_manual.md"
CLIENT_ACTIONS_SIM_FILE = AGENTS_DIR / "client_actions_sim.json"
CLIENT_ACTIONS_COACH_FILE = AGENTS_DIR / "client_actions_coach.json"

# ---------------------------------------------------------------------------
# In-memory transcript store
# ---------------------------------------------------------------------------
_transcripts: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Vocal Bridge config
# ---------------------------------------------------------------------------
VB_API_URL = os.environ.get("VB_API_URL", "https://vocalbridgeai.com")
VB_TOKEN_ENDPOINT = f"{VB_API_URL}/api/v1/token"

SIMULATION_AGENT_NAME = "VoiceCoach Customer"
COACHING_AGENT_NAME = "VoiceCoach Coach"

# Agent IDs populated at startup
_sim_agent_id: str | None = None
_coach_agent_id: str | None = None


# ---------------------------------------------------------------------------
# VB CLI helpers
# ---------------------------------------------------------------------------

def _find_vb() -> str:
    venv_vb = Path(__file__).resolve().parent / ".venv" / "bin" / "vb"
    if venv_vb.exists():
        return str(venv_vb)
    vb_path = shutil.which("vb")
    if not vb_path:
        raise RuntimeError("vb CLI not found on PATH or in .venv")
    return vb_path


def _run_vb(args: list[str]) -> subprocess.CompletedProcess:
    with tracer.start_as_current_span("vb_cli", attributes={"vb.command": " ".join(args[:2])}) as span:
        vb = _find_vb()
        result = subprocess.run([vb] + args, capture_output=True, text=True)
        if result.returncode != 0:
            error_msg = f"vb CLI error ({' '.join(args[:2])}): {result.stderr[:500]}"
            span.set_status(StatusCode.ERROR, error_msg)
            raise RuntimeError(error_msg)
        return result


def _run_vb_json(args: list[str]) -> dict:
    result = _run_vb(args + ["--json"])
    stdout = result.stdout.strip()
    if not stdout:
        logger.warning("vb CLI returned empty response for: vb %s", " ".join(args))
        return {}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        logger.warning(
            "vb CLI returned non-JSON for 'vb %s': %s", " ".join(args), stdout[:200]
        )
        return {}


def _inject_manual(prompt_text: str) -> str:
    if EMPLOYEE_MANUAL_FILE.exists():
        manual_text = EMPLOYEE_MANUAL_FILE.read_text()
        return prompt_text.replace("{{EMPLOYEE_MANUAL}}", manual_text)
    return prompt_text


def _find_agent_by_name(name: str) -> str | None:
    """Return agent ID if an agent with the given name exists, else None."""
    data = _run_vb_json(["agent", "list"])
    for agent in data.get("agents", []):
        if agent.get("name") == name:
            return agent["id"]
    return None


def _ensure_agent(
    name: str,
    style: str,
    prompt_file: Path,
    client_actions_file: Path,
    greeting: str,
    model_settings: dict,
) -> str:
    """Find or create a VB agent by name. Returns agent ID.

    NOTE: `vb config set` / `vb prompt set` always target the *account-level*
    default agent, NOT the agent selected by `vb agent use`.  All configuration
    must be passed at creation time via `vb agent create` flags.  Existing agents
    cannot be updated through the CLI — update them in the Vocal Bridge portal.
    """
    with tracer.start_as_current_span("ensure_agent") as span:
        span.set_attribute("agent.name", name)
        try:
            agent_id = _find_agent_by_name(name)

            if agent_id is None:
                span.set_attribute("agent.created", True)
                # Create the agent — pass ALL config here; CLI has no update command.
                prompt_text = _inject_manual(prompt_file.read_text())
                with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as pf:
                    pf.write(prompt_text)
                    prompt_path = pf.name
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as mf:
                    json.dump(model_settings, mf)
                    settings_path = mf.name
                try:
                    data = _run_vb_json([
                        "agent", "create",
                        "--name", name,
                        "--style", style,
                        "--prompt-file", prompt_path,
                        "--greeting", greeting,
                        "--client-actions-file", str(client_actions_file),
                        "--model-settings-file", settings_path,
                    ])
                    agent_id = data.get("id") or data.get("agent", {}).get("id")
                finally:
                    os.unlink(prompt_path)
                    os.unlink(settings_path)

                if not agent_id:
                    agent_id = _find_agent_by_name(name)

                if not agent_id:
                    raise RuntimeError(f"Could not determine ID for newly created agent '{name}'")

                logger.info("Created agent '%s' → %s", name, agent_id)
            else:
                span.set_attribute("agent.created", False)
                logger.info("Agent '%s' already exists → %s (update via VB portal if needed)", name, agent_id)

            span.set_attribute("agent.id", agent_id)
            return agent_id
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


def _setup_agents() -> None:
    """Initialize both VB agents at startup with their permanent prompts and config."""
    global _sim_agent_id, _coach_agent_id

    with tracer.start_as_current_span("setup_agents") as span:
        logger.info("Configuring Simulation Agent…")
        _sim_agent_id = _ensure_agent(
            name=SIMULATION_AGENT_NAME,
            style="Chatty",
            prompt_file=SIMULATION_PROMPT_FILE,
            client_actions_file=CLIENT_ACTIONS_SIM_FILE,
            greeting="Hi, I'm a customer calling in to customer service. Let me know when you're ready and I'll tell you what I'm calling about.",
            model_settings={"tts_voice": "cedar"},
        )

        logger.info("Configuring Coaching Agent…")
        _coach_agent_id = _ensure_agent(
            name=COACHING_AGENT_NAME,
            style="Focused",
            prompt_file=COACHING_PROMPT_FILE,
            client_actions_file=CLIENT_ACTIONS_COACH_FILE,
            greeting="Hello! I have your session results here. Let's walk through your call together.",
            model_settings={"tts_voice": "VR6AewLTigWG4xSOukaG", "voice_style": "professional"},
        )

        logger.info("Agents ready — sim=%s coach=%s", _sim_agent_id, _coach_agent_id)
        span.set_attribute("agent.sim_id", _sim_agent_id or "")
        span.set_attribute("agent.coach_id", _coach_agent_id or "")


# ---------------------------------------------------------------------------
# Lifespan — run agent setup at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    try:
        _setup_agents()
    except Exception as exc:
        logger.error("Agent setup failed: %s", exc, exc_info=True)
        logger.warning("App will start anyway; sessions may fail if agents are not configured.")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-instrument FastAPI routes with OpenTelemetry spans.
# With browser-side OTel, the traceparent header propagates trace context
# so backend spans automatically parent under the browser’s trace.
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
except Exception:
    logger.debug("FastAPI OTel instrumentation not available")

# Auto-instrument outbound HTTP calls (Vocal Bridge, OpenAI)
try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    HTTPXClientInstrumentor().instrument()
except Exception:
    logger.debug("HTTPX OTel instrumentation not available")


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class SessionRequest(BaseModel):
    scenario_id: str
    participant_name: str = "Web User"
    trace_session_id: str | None = None


class TranscriptEntry(BaseModel):
    role: str
    text: str
    timestamp: str | None = None


class TranscriptRequest(BaseModel):
    scenario_id: str
    transcript: list[TranscriptEntry]
    trace_session_id: str | None = None


class CoachingRequest(BaseModel):
    session_id: str | None = None
    scenario_id: str | None = None
    transcript: list[TranscriptEntry] | None = None
    trace_session_id: str | None = None


class CoachingSessionRequest(BaseModel):
    scenario_id: str | None = None
    participant_name: str = "Web User"
    trace_session_id: str | None = None


# ---------------------------------------------------------------------------
# 0. Health check
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    if not _sim_agent_id or not _coach_agent_id:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": "agents not initialized"},
        )
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# 1. GET /api/scenarios — trainee-visible fields only
# ---------------------------------------------------------------------------

@app.get("/api/scenarios")
async def get_scenarios():
    if not SCENARIOS_FILE.exists():
        raise HTTPException(status_code=500, detail="scenarios.json not found")
    scenarios = json.loads(SCENARIOS_FILE.read_text())
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "difficulty": s["difficulty"],
            "description": s["description"],
        }
        for s in scenarios
    ]


# ---------------------------------------------------------------------------
# VB token helper
# ---------------------------------------------------------------------------

async def _get_vb_token(participant_name: str, api_key: str, agent_id: str = "") -> dict:
    """Get a LiveKit token from Vocal Bridge.

    The API key determines which agent the session connects to:
    - Agent-scoped keys (from agent detail page) → routes to that agent.
    - Account-scoped keys → routes to the account default agent.
    """
    with tracer.start_as_current_span("vb_token_request") as span:
        span.set_attribute("participant.name", participant_name)
        span.set_attribute("agent.id", agent_id)
        try:
            if not api_key:
                raise HTTPException(status_code=500, detail="VB API key not configured")

            headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
            payload = {"participant_name": participant_name}

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(VB_TOKEN_ENDPOINT, json=payload, headers=headers)

            if resp.status_code != 200:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"Vocal Bridge API error: {resp.text[:500]}",
                )
            return resp.json()
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


# ---------------------------------------------------------------------------
# 2. POST /api/session — select simulation agent + get LiveKit token
# ---------------------------------------------------------------------------

@app.post("/api/session")
async def create_session(req: SessionRequest):
    with tracer.start_as_current_span("create_session") as span:
        span.set_attribute("scenario.id", req.scenario_id)
        span.set_attribute("session.phase", "simulation")
        if req.trace_session_id:
            span.set_attribute("session.id", req.trace_session_id)
        try:
            if not SCENARIOS_FILE.exists():
                raise HTTPException(status_code=500, detail="scenarios.json not found")
            scenarios = json.loads(SCENARIOS_FILE.read_text())
            scenario = next((s for s in scenarios if s["id"] == req.scenario_id), None)
            if not scenario:
                raise HTTPException(status_code=404, detail=f"Scenario '{req.scenario_id}' not found")

            if not _sim_agent_id:
                raise HTTPException(status_code=500, detail="Simulation agent not initialized")

            sim_key = os.environ.get("VB_SIM_API_KEY") or os.environ.get("VB_API_KEY", "")
            data = await _get_vb_token(req.participant_name, api_key=sim_key, agent_id=_sim_agent_id or "")

            return {
                "livekit_url": data["livekit_url"],
                "token": data["token"],
                "room_name": data.get("room_name"),
                "scenario_context": {
                    "scenario_id": scenario["id"],
                    "customer_name": scenario.get("customer_name", ""),
                    "persona": scenario.get("persona", {}),
                    "goal": scenario.get("goal", ""),
                    "behavior": scenario.get("behavior", ""),
                    "actor_strategy": scenario.get("actor_strategy", ""),
                    "opening_line": scenario.get("opening_line", ""),
                },
            }
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


# ---------------------------------------------------------------------------
# 3. POST /api/coaching-session — select coaching agent + get LiveKit token
# ---------------------------------------------------------------------------

@app.post("/api/coaching-session")
async def create_coaching_session(req: CoachingSessionRequest):
    with tracer.start_as_current_span("create_coaching_session") as span:
        span.set_attribute("scenario.id", req.scenario_id or "")
        span.set_attribute("session.phase", "coaching")
        if req.trace_session_id:
            span.set_attribute("session.id", req.trace_session_id)
        try:
            if not _coach_agent_id:
                raise HTTPException(status_code=500, detail="Coaching agent not initialized")

            coach_key = os.environ.get("VB_COACH_API_KEY") or os.environ.get("VB_API_KEY", "")
            data = await _get_vb_token(req.participant_name, api_key=coach_key, agent_id=_coach_agent_id or "")
            return {
                "livekit_url": data["livekit_url"],
                "token": data["token"],
                "room_name": data.get("room_name"),
            }
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


# ---------------------------------------------------------------------------
# 4. POST /api/transcript — store transcript in memory
# ---------------------------------------------------------------------------

@app.post("/api/transcript")
async def store_transcript(req: TranscriptRequest):
    with tracer.start_as_current_span("store_transcript") as span:
        span.set_attribute("scenario.id", req.scenario_id)
        span.set_attribute("session.phase", "simulation")
        session_id = str(uuid.uuid4())
        span.set_attribute("session.id", session_id)
        _transcripts[session_id] = {
            "scenario_id": req.scenario_id,
            "transcript": [t.model_dump() for t in req.transcript],
        }
        return {"session_id": session_id, "status": "received"}


# ---------------------------------------------------------------------------
# 5. POST /api/coaching — Feedback Agent: evaluate transcript via LLM
# ---------------------------------------------------------------------------

def _build_feedback_messages(scenario_id: str, transcript: list[dict]) -> list[dict]:
    """Build OpenAI messages for the Feedback Agent analysis."""
    with tracer.start_as_current_span("build_feedback_messages") as span:
        span.set_attribute("scenario.id", scenario_id)
        system_prompt = FEEDBACK_PROMPT_FILE.read_text() if FEEDBACK_PROMPT_FILE.exists() else ""
        system_prompt = _inject_manual(system_prompt)

        scenario_context = ""
        if SCENARIOS_FILE.exists():
            scenarios = json.loads(SCENARIOS_FILE.read_text())
            match = next((s for s in scenarios if s["id"] == scenario_id), None)
            if match:
                scenario_context = (
                    f"\n\n## Scenario Context\n"
                    f"- Title: {match['title']}\n"
                    f"- Difficulty: {match['difficulty']}\n"
                    f"- Description: {match['description']}\n"
                    f"- Customer Name: {match.get('customer_name', 'Unknown')}\n"
                    f"- Manual Sections Tested: {', '.join(match.get('manual_sections_tested', []))}\n"
                )

        transcript_text = "\n".join(
            f"[{t.get('timestamp', '')}] {t['role']}: {t['text']}" for t in transcript
        )

        return [
            {"role": "system", "content": system_prompt + scenario_context},
            {"role": "user", "content": f"Here is the transcript to evaluate:\n\n{transcript_text}\n\nProvide your evaluation as JSON."},
        ]


def _mock_coaching_response() -> dict:
    return {
        "scenario_id": "mock",
        "scenario_title": "Mock Evaluation",
        "difficulty": "N/A",
        "scores": [
            {"category": "Greeting Protocol", "manual_section": "§1.1", "score": 8, "max_score": 10, "summary": "Mock: Good greeting.", "applicable": True},
            {"category": "Active Listening", "manual_section": "§1.2", "score": 7, "max_score": 10, "summary": "Mock: Decent listening.", "applicable": True},
            {"category": "Product Knowledge", "manual_section": "§4.1, §4.2", "score": 8, "max_score": 10, "summary": "Mock: Solid product knowledge.", "applicable": True},
            {"category": "De-escalation (HEAT)", "manual_section": "§3.1", "score": None, "max_score": 10, "summary": "Not applicable.", "applicable": False},
            {"category": "Goodwill Gesture", "manual_section": "§3.2", "score": None, "max_score": 10, "summary": "Not applicable.", "applicable": False},
            {"category": "Escalation Handling", "manual_section": "§3.3", "score": None, "max_score": 10, "summary": "Not applicable.", "applicable": False},
            {"category": "Policy Compliance", "manual_section": "§2.1, §5.1", "score": 9, "max_score": 10, "summary": "Mock: Followed policies.", "applicable": True},
            {"category": "Closing Protocol", "manual_section": "§1.3", "score": 7, "max_score": 10, "summary": "Mock: Adequate closing.", "applicable": True},
        ],
        "overall_score": 7.8,
        "improvement_areas": [
            {"area": "Use the customer's name more often", "detail": "Per §1.1, if the customer provides their name, use it throughout the call."},
            {"area": "Summarize actions before closing", "detail": "Per §1.3, always recap every action taken before saying goodbye."},
        ],
        "coaching_dialogue": "Overall, a solid interaction at 7.8. Let's walk through what went well and where there's room to grow.",
    }


@app.post("/api/coaching")
async def get_coaching(req: CoachingRequest):
    with tracer.start_as_current_span("get_coaching") as span:
        span.set_attribute("session.phase", "feedback")
        if req.trace_session_id:
            span.set_attribute("session.id", req.trace_session_id)
        try:
            if req.session_id and req.session_id in _transcripts:
                stored = _transcripts[req.session_id]
                scenario_id = stored["scenario_id"]
                transcript = stored["transcript"]
                span.set_attribute("session.id", req.session_id)
            elif req.transcript and req.scenario_id:
                scenario_id = req.scenario_id
                transcript = [t.model_dump() for t in req.transcript]
            else:
                raise HTTPException(status_code=400, detail="Provide session_id or (scenario_id + transcript)")

            span.set_attribute("scenario.id", scenario_id)

            openai_key = os.environ.get("OPENAI_API_KEY", "")
            if not openai_key:
                span.set_attribute("coaching.mock", True)
                return _mock_coaching_response()

            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=openai_key)
            messages = _build_feedback_messages(scenario_id, transcript)

            with tracer.start_as_current_span("openai_chat_completion") as oai_span:
                oai_span.set_attribute("openai.model", "gpt-5.4")
                completion = await client.chat.completions.create(
                    model="gpt-5.4",
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.3,
                )

            try:
                result = json.loads(completion.choices[0].message.content)
            except (json.JSONDecodeError, IndexError):
                result = _mock_coaching_response()
                result["_note"] = "LLM response was not valid JSON, returning mock"

            return result
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
