# Vocal Bridge — Hello World Voice Agent

A minimal voice agent built on [Vocal Bridge](https://vocalbridgeai.com), a higher-level abstraction over LiveKit for building voice AI agents.

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- A Vocal Bridge account ([sign up here](https://vocalbridgeai.com/auth/signup))
- A Vocal Bridge API key (starts with `vb_`, e.g. `vb_abc123xyz`)

## Project Structure

```
vocal-bridge-hello-world/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env.example           # Template for environment variables
├── config.py              # Agent configuration constants
├── setup_agent.py         # Creates and configures the agent via the vb CLI
├── run_agent.py           # Starts a voice session via CLI
├── server.py              # Backend server — serves web UI & proxies VB API
└── web_embed/             # Browser-based voice client (LiveKit WebRTC)
    ├── index.html
    └── app.js
```

## Quick Start

### 1. Create a Virtual Environment and Install Dependencies

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

This creates a `.venv`, activates it, and installs the `vb` CLI tool (current version 0.7.1) along with other dependencies.

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your actual API key:

```
VB_API_KEY=vb_your_actual_key_here
```

> **Where to get your API key:** Go to your agent's page on [vocalbridgeai.com](https://vocalbridgeai.com), open **Developer Mode**, and click **"Create API Key"** in the API Keys section. Keys use the `vb_` prefix.

### 3. Authenticate the CLI

```bash
vb auth login
```

Follow the prompts to authenticate. This stores your credentials locally so subsequent `vb` commands work without re-authenticating.

### 4. Create the Agent

```bash
python setup_agent.py
```

This script uses the `vb` CLI to:
- Create an agent named **"Hello World Agent"** with a Chatty style
- Configure max call duration, history messages, and debug mode

### 5. Verify the Agent

```bash
vb agent
```

You should see your agent listed with its Name, Mode, and Status.

### 6. Run the Agent

```bash
python run_agent.py
```

This starts a voice session with your Hello World Agent.

### 7. Check Logs

```bash
vb logs
```

Review session logs to see what happened during your voice session.

### 8. Troubleshoot (if needed)

```bash
vb debug
```

Streams real-time debug events so you can diagnose any issues.

## Configuration

View all current settings:

```bash
vb config show
```

Update a setting:

```bash
vb config set --debug-mode true
vb config set --max-call-duration 10
```

See [config.py](config.py) for all configurable parameters used by this project.

## Web Embed (Voice in the Browser)

The `web_embed/` directory is a browser-based voice client that connects to your Vocal Bridge agent via LiveKit WebRTC. The `server.py` backend handles authentication and serves the UI.

### How to run it

```bash
# Make sure your .venv is active and .env has your VB_API_KEY
python server.py
# Open http://localhost:8000 in your browser
```

Click **Start Conversation**, allow microphone access, and talk to your agent.

### Architecture

```
Browser (app.js)          server.py              Vocal Bridge API
     │                        │                        │
     │  POST /api/session     │                        │
     │───────────────────────>│  POST /api/v1/token    │
     │                        │───────────────────────>│
     │                        │ {livekit_url, token}   │
     │ {livekit_url, token}   │<───────────────────────│
     │<───────────────────────│                        │
     │                                                 │
     │  LiveKit WebRTC (audio + transcript data channel) │
     │<═══════════════════════════════════════════════>│
```

## API Reference

The backend calls a single endpoint:

```
POST http://vocalbridgeai.com/api/v1/token
Headers:  X-API-Key: vb_your_key
Body:     {"participant_name": "Web User"}

Response: {
  "livekit_url": "wss://….livekit.cloud",
  "token": "eyJhbGciOiJIUzI1NiJ9…",
  "room_name": "user-abc-agent-xyz-api-12345",
  "participant_identity": "api-client-xxxx-12345",
  "expires_in": 3600,
  "agent_mode": "cascaded_concierge"
}
```

See the full [Developer Guide](https://vocalbridgeai.com/docs/developer-guide) for additional endpoints, client actions, live transcript, MCP tools, and more.

## Resources

- [Vocal Bridge Developer Guide](https://vocalbridgeai.com/docs/developer-guide)
- [PyPI: vocal-bridge](https://pypi.org/project/vocal-bridge/) (CLI)
- [LiveKit JS Client SDK](https://docs.livekit.io/client-sdk-js/)
- [LiveKit Documentation](https://docs.livekit.io/)
