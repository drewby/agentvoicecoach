# 🎙 VoiceCoach — AI-Powered Customer Service Training Simulator

> **Origin:** VoiceCoach started at the [DeepLearning.AI Global Builder Night — Tokyo](https://lu.ma/) (March 23, 2026), hosted at Google for Startups Campus, Shibuya. The project skeleton and dev environment were prepared beforehand; the solution concept, product definition, and a working MVP were completed during the 2-hour build session. Development has continued since — adding full OpenTelemetry observability, improved agent prompts, and coaching session refinements.

## The Problem

Customer service is a high-turnover function across many industries. Front-line managers pour resources into onboarding and training new representatives — only to see them leave weeks or months later. Traditional training methods (shadowing, scripts, role-play with peers) are expensive, inconsistent, and hard to scale.

## The Solution

VoiceCoach uses AI to make that training instant, repeatable, and self-serve. A simulated AI customer engages the trainee in a realistic live voice conversation, then an AI coach evaluates their performance against the company employee manual and walks them through what they did well and where to improve — all by voice. No human trainer required.

## 🎬 Demo

[![VoiceCoach Demo](https://img.youtube.com/vi/SrRxwKzfPmw/maxresdefault.jpg)](https://youtu.be/SrRxwKzfPmw)

## Architecture

```mermaid
graph TB
    subgraph Browser["🖥️ Browser"]
        UI["SPA<br/>(HTML/CSS/JS)"]
        LK1["LiveKit Client<br/>(WebRTC Audio)"]
    end

    subgraph Aspire["☁️ .NET Aspire AppHost"]
        direction TB
        FE["⚛️ Frontend<br/>Express.js<br/>(HTTPS + API Proxy)"]
        BE["🔧 Backend<br/>FastAPI / Python<br/>(HTTP)"]
    end

    subgraph External["🌐 External Services"]
        VB["🎤 Vocal Bridge<br/>(Voice Agent Platform)"]
        LKS["🔊 LiveKit Cloud<br/>(WebRTC Server)"]
        OAI["🧠 OpenAI<br/>gpt-5.4"]
    end

    UI -->|"HTTPS"| FE
    FE -->|"/api/* proxy (HTTP)"| BE
    LK1 <-->|"WebRTC Audio"| LKS

    BE -->|"1. Configure agent<br/>(vb CLI)"| VB
    BE -->|"2. Get token<br/>(REST API)"| VB
    VB -->|"Voice session"| LKS
    BE -->|"Evaluate transcript"| OAI

    style Browser fill:#1a1b2e,stroke:#6c63ff,color:#f0f0f5
    style Aspire fill:#0f1023,stroke:#22c55e,color:#f0f0f5
    style External fill:#0f1023,stroke:#f59e0b,color:#f0f0f5
```

### Flow

```mermaid
sequenceDiagram
    participant T as Trainee (Browser)
    participant FE as Frontend
    participant BE as Backend
    participant VB as Vocal Bridge
    participant LK as LiveKit
    participant AI as OpenAI

    T->>FE: Select scenario
    FE->>BE: POST /api/session
    BE->>VB: Configure agent (prompt, voice, greeting)
    BE->>VB: POST /api/v1/token
    VB-->>BE: LiveKit token + URL
    BE-->>FE: Token
    FE->>LK: Connect WebRTC
    LK-->>T: 🔊 AI Customer speaks opening line

    Note over T,LK: Live voice conversation

    T->>FE: Click "End Simulation"
    FE->>BE: POST /api/transcript
    FE->>BE: POST /api/coaching
    BE->>AI: Evaluate transcript (gpt-5.4)
    AI-->>BE: Structured evaluation JSON
    BE-->>FE: Scores + feedback
    FE-->>T: 📊 Show evaluation results

    T->>FE: Click "Start Coaching Session"
    FE->>BE: POST /api/coaching-session (with eval data)
    BE->>VB: Reconfigure agent (coach prompt, voice, eval context)
    BE->>VB: POST /api/v1/token
    VB-->>BE: LiveKit token
    BE-->>FE: Token
    FE->>LK: Connect WebRTC (new room)
    LK-->>T: 🎓 AI Coach discusses performance
```

## Features

- **3 training scenarios** with increasing difficulty (Easy → Medium → Hard)
- **Distinct AI customer voices** per scenario using ElevenLabs TTS
- **Live voice simulation** via Vocal Bridge + LiveKit WebRTC
- **AI-powered evaluation** using OpenAI gpt-5.4 with structured JSON scoring
- **8-category scoring rubric** grounded in the employee manual
- **Voice coaching session** — an AI coach discusses your performance after scoring
- **Aspire orchestration** — one command runs everything

## 📡 Observability

VoiceCoach is instrumented with [OpenTelemetry](https://opentelemetry.io/) across both browser and backend, with traces and log records flowing into the [.NET Aspire dashboard](https://learn.microsoft.com/dotnet/aspire). Each session phase (simulation, feedback, coaching) produces a structured trace with child spans for real work — API calls, room connections, conversations — and transcript turns emitted as OTel log records correlated to the active span.

![Aspire simulation trace](docs/Aspire%20screenshot.png)

The [Aspire MCP server](https://www.nuget.org/packages/Aspire.Dashboard.MCP) was key to our development workflow — Squad agents could query traces and structured logs programmatically, inspect conversation transcripts turn by turn, and identify issues without manual dashboard browsing. For example, examining a simulation trace revealed the agent wasting its first turn with a generic preamble instead of the scripted persona, garbled STT noise mixed into real turns, and a coaching agent going silent mid-session. Each issue was visible directly in the `transcript_turn` log records on the `conversation` span.

> See [docs/telemetry-architecture.md](docs/telemetry-architecture.md) for the full design, trace structure, and attribute conventions.

## Prerequisites

- [.NET 10 SDK](https://dotnet.microsoft.com/download) (for Aspire)
- [Node.js 18+](https://nodejs.org/) (for the frontend)
- [Python 3.11+](https://www.python.org/) (for the backend)
- [Aspire CLI](https://learn.microsoft.com/dotnet/aspire) (`dotnet tool install -g aspirecli`)
- A [Vocal Bridge](https://vocalbridgeai.com) account and API key
- An [OpenAI](https://platform.openai.com) API key (for transcript evaluation)

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/drewby/agentvoicecoach.git
cd agentvoicecoach
```

### 2. Set up the Python backend

```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ../..
```

### 3. Install frontend dependencies

```bash
cd src/frontend
npm install
cd ../..
```

### 4. Generate dev certificates

```bash
mkdir -p tmp
dotnet dev-certs https --export-path tmp/localhost.crt --format PEM
cp tmp/localhost.crt tmp/localhost.key  # Or generate a proper key pair
```

> See [docs/dev-certificates.md](docs/dev-certificates.md) for full instructions on trusting the dev cert in your browser.

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
VB_API_KEY=vb_your_vocal_bridge_api_key
OPENAI_API_KEY=sk-your_openai_api_key
```

| Variable | Required | Description |
|----------|----------|-------------|
| `VB_API_KEY` | Yes | Vocal Bridge API key (starts with `vb_`) — get one at [vocalbridgeai.com](https://vocalbridgeai.com/auth/signup) |
| `OPENAI_API_KEY` | No* | OpenAI API key for gpt-5.4 transcript evaluation. *Without it, mock evaluation data is returned.* |

### 6. Run with Aspire

```bash
cd src/VoiceProject.AppHost
aspire run
```

Aspire will:
- Build and start the Python backend (HTTP)
- Build and start the Express frontend (HTTPS)
- Wire up service discovery and environment variables
- Open the Aspire dashboard

Look for the frontend URL in the output (e.g., `https://localhost:XXXXX`) and open it in your browser.

## Project Structure

```
├── .env.example                 # Environment variable template
├── src/
│   ├── VoiceProject.AppHost/    # .NET Aspire orchestrator
│   │   └── Program.cs           # Resource definitions
│   ├── backend/                 # Python FastAPI backend
│   │   ├── main.py              # API endpoints
│   │   ├── requirements.txt
│   │   └── agents/              # Agent configuration
│   │       ├── simulation_prompt.md
│   │       ├── coaching_prompt.md
│   │       ├── employee_manual.md
│   │       ├── scenarios.json
│   │       ├── config.py
│   │       └── client_actions_*.json
│   └── frontend/                # Express + vanilla JS frontend
│       ├── server.js            # HTTPS server + API proxy
│       └── public/
│           └── index.html       # Single-page application
├── docs/
│   ├── voicecoach-plan.md       # Development plan
│   └── dev-certificates.md      # HTTPS cert setup guide
└── infra/                       # Azure Bicep templates
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/scenarios` | List available training scenarios |
| `POST` | `/api/session` | Configure VB agent + get LiveKit token for simulation |
| `POST` | `/api/transcript` | Store simulation transcript |
| `POST` | `/api/coaching` | Evaluate transcript via OpenAI gpt-5.4 |
| `POST` | `/api/coaching-session` | Configure VB agent + get token for coaching voice call |

## 🤖 Built by Squad

This project was built with [Squad](https://github.com/bradygaster/squad) — an AI team orchestration system that runs inside GitHub Copilot. Squad assembles a team of specialized AI agents, each with a distinct role, persistent memory, and defined areas of ownership. A coordinator routes work to agents in parallel, tracks decisions, and keeps the pipeline moving — much like a real engineering team, but completing a full hackathon build in a couple hours.

The team for this project was cast from the *Inception* universe:

| Agent | Role | Contributions |
|-------|------|---------------|
| 🎯 **Cobb** | Product Manager | Created the 6-phase, 32-item development plan. Designed the architecture mapping from Vocal Bridge patterns to our project structure. Made key technical decisions: coaching approach (Vocal Bridge for simulation, LLM for evaluation), frontend transcript accumulation, and `session_context` client action for scenario injection. |
| 🏗️ **Arthur** | Project Lead | Set up the project structure with .NET Aspire AppHost orchestration. Configured the polyglot setup (Python backend + Node frontend) under a single Aspire umbrella. Coordinated cross-agent work and maintained the GitHub repository. |
| 🎨 **Ariadne** | UI/UX Designer | Available for design consultation and UX review during development. |
| ⚛️ **Eames** | Frontend Dev | Built the entire 3-screen single-page application (scenario picker → voice simulation → coaching results). Integrated LiveKit WebRTC for real-time voice, implemented the dark UI theme, built the Express HTTPS server with API proxy, and added the coaching voice call UI with a second LiveKit connection. |
| 🔧 **Yusuf** | Backend Dev | Built all 5 FastAPI endpoints. Implemented dynamic Vocal Bridge agent reconfiguration per scenario (prompt, voice, greeting, client actions via CLI). Built the OpenAI gpt-5.4 evaluation pipeline with structured JSON scoring, the coaching session endpoint, and the VB token acquisition helpers. |
| 🧪 **Saito** | Tester / QA | Available for test case design and quality assurance review. |
| ⚙️ **Browning** | Build / Infra | Scaffolded Azure Bicep templates and GitHub Actions. Configured dev container with HTTPS certificates and python3-venv fix. Installed Vocal Bridge CLI, set up `.env` configuration, and wired environment variables through the Aspire AppHost. |
| 📋 **Scribe** | Session Logger | Maintained the decision ledger, orchestration logs, and cross-agent context sharing throughout the session. |
| 🔄 **Ralph** | Work Monitor | Tracked the work queue and kept the team pipeline moving. |

> The Squad coordinator (powered by GitHub Copilot) ran parallel fan-outs — spawning multiple agents simultaneously to build the backend, frontend, infrastructure, and agent prompts in a single turn, then collecting results and chaining follow-up work automatically.

## License

MIT
