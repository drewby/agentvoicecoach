import json
import os
import uuid
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
AGENTS_DIR = Path(__file__).resolve().parent / "agents"
SCENARIOS_FILE = AGENTS_DIR / "scenarios.json"
COACHING_PROMPT_FILE = AGENTS_DIR / "coaching_prompt.md"
EMPLOYEE_MANUAL_FILE = AGENTS_DIR / "employee_manual.md"

# ---------------------------------------------------------------------------
# In-memory transcript store
# ---------------------------------------------------------------------------
_transcripts: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Vocal Bridge config
# ---------------------------------------------------------------------------
VB_API_URL = os.environ.get("VB_API_URL", "https://vocalbridgeai.com")
VB_TOKEN_ENDPOINT = f"{VB_API_URL}/api/v1/token"

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class SessionRequest(BaseModel):
    scenario_id: str
    participant_name: str = "Web User"

class TranscriptEntry(BaseModel):
    role: str
    text: str
    timestamp: str | None = None

class TranscriptRequest(BaseModel):
    scenario_id: str
    transcript: list[TranscriptEntry]

class CoachingRequest(BaseModel):
    session_id: str | None = None
    scenario_id: str | None = None
    transcript: list[TranscriptEntry] | None = None


# ---------------------------------------------------------------------------
# 0. Health check
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
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
# 2. POST /api/session — get LiveKit token from Vocal Bridge
# ---------------------------------------------------------------------------

@app.post("/api/session")
async def create_session(req: SessionRequest):
    api_key = os.environ.get("VB_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="VB_API_KEY not configured")

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }
    payload = {"participant_name": req.participant_name}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(VB_TOKEN_ENDPOINT, json=payload, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Vocal Bridge API error: {resp.text[:500]}",
        )

    data = resp.json()
    return {
        "livekit_url": data["livekit_url"],
        "token": data["token"],
        "room_name": data.get("room_name"),
    }


# ---------------------------------------------------------------------------
# 3. POST /api/transcript — store transcript in memory
# ---------------------------------------------------------------------------

@app.post("/api/transcript")
async def store_transcript(req: TranscriptRequest):
    session_id = str(uuid.uuid4())
    _transcripts[session_id] = {
        "scenario_id": req.scenario_id,
        "transcript": [t.model_dump() for t in req.transcript],
    }
    return {"session_id": session_id, "status": "received"}


# ---------------------------------------------------------------------------
# 4. POST /api/coaching — evaluate transcript via LLM
# ---------------------------------------------------------------------------

def _build_coaching_messages(scenario_id: str, transcript: list[dict]) -> list[dict]:
    system_prompt = COACHING_PROMPT_FILE.read_text() if COACHING_PROMPT_FILE.exists() else ""

    # Inject employee manual into the prompt template
    if EMPLOYEE_MANUAL_FILE.exists():
        manual_text = EMPLOYEE_MANUAL_FILE.read_text()
        system_prompt = system_prompt.replace("{{EMPLOYEE_MANUAL}}", manual_text)

    # Load scenario context for the coaching prompt
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
            {"category": "Greeting Protocol", "manual_section": "§1.1", "score": 8, "max_score": 10, "summary": "Mock: Good greeting."},
            {"category": "Active Listening", "manual_section": "§1.2", "score": 7, "max_score": 10, "summary": "Mock: Decent listening."},
            {"category": "Product Knowledge", "manual_section": "§4.1, §4.2", "score": 8, "max_score": 10, "summary": "Mock: Solid product knowledge."},
            {"category": "Policy Compliance", "manual_section": "§2.1, §5.1", "score": 9, "max_score": 10, "summary": "Mock: Followed policies."},
            {"category": "Closing Protocol", "manual_section": "§1.3", "score": 7, "max_score": 10, "summary": "Mock: Adequate closing."},
        ],
        "overall_score": 7.8,
        "improvement_areas": [
            "Try using the customer's name more often",
            "Summarize actions taken before closing",
        ],
        "coaching_dialogue": "Overall, a solid interaction. Focus on closing protocol — always summarize actions and confirm the customer has no more questions.",
    }


@app.post("/api/coaching")
async def get_coaching(req: CoachingRequest):
    # Resolve transcript — either from session store or from request body
    if req.session_id and req.session_id in _transcripts:
        stored = _transcripts[req.session_id]
        scenario_id = stored["scenario_id"]
        transcript = stored["transcript"]
    elif req.transcript and req.scenario_id:
        scenario_id = req.scenario_id
        transcript = [t.model_dump() for t in req.transcript]
    else:
        raise HTTPException(status_code=400, detail="Provide session_id or (scenario_id + transcript)")

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_key:
        # Return mock so frontend can still develop
        return _mock_coaching_response()

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=openai_key)
    messages = _build_coaching_messages(scenario_id, transcript)

    completion = await client.chat.completions.create(
        model="gpt-4o",
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
    )
