#!/usr/bin/env python3
"""
Start a voice session with the Vocal Bridge Hello World agent.

Two approaches are provided:
  A) REST API — calls POST /api/v1/token to get a LiveKit room token
  B) CLI subprocess — uses confirmed vb commands

Prerequisites:
  1. uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
  2. cp .env.example .env   # add your VB_API_KEY
  3. python setup_agent.py  # create the agent first (or create via dashboard)
"""

import os
import shutil
import subprocess
import sys

from dotenv import load_dotenv

from config import DEFAULT_CONFIG

load_dotenv()


def get_api_key() -> str:
    """Load and validate the Vocal Bridge API key from the environment."""
    api_key = os.environ.get("VB_API_KEY", "")
    if not api_key or not api_key.startswith("vb_"):
        print(
            "Error: VB_API_KEY is missing or invalid.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Set VB_API_KEY to your key (starts with vb_)\n"
            "  3. Get a key at https://vocalbridgeai.com/auth/signup",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


# ---------------------------------------------------------------------------
# Approach A: REST API — POST /api/v1/token
# See: https://vocalbridgeai.com/docs/developer-guide#api-reference
# ---------------------------------------------------------------------------

def start_session_rest_api(api_key: str) -> None:
    """
    Call the Vocal Bridge token endpoint and print the LiveKit connection info.

    POST http://vocalbridgeai.com/api/v1/token
    Headers: X-API-Key: vb_…
    Body: {"participant_name": "CLI User"}
    Response: {"livekit_url": "wss://…", "token": "eyJ…", "room_name": "…", …}
    """
    import requests

    base_url = os.environ.get("VB_API_URL", "http://vocalbridgeai.com")
    token_url = f"{base_url}/api/v1/token"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }
    payload = {"participant_name": "CLI User"}

    print(f"POST {token_url}")
    print(f"Payload: {payload}\n")

    try:
        response = requests.post(token_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("Token received successfully:\n")
        print(f"  LiveKit URL:  {data['livekit_url']}")
        print(f"  Room:         {data.get('room_name', 'N/A')}")
        print(f"  Agent mode:   {data.get('agent_mode', 'N/A')}")
        print(f"  Expires in:   {data.get('expires_in', 'N/A')}s")
        print(f"  Token:        {data['token'][:40]}…")
        print()
        print("Use this token with the LiveKit client SDK to connect.")
        print("Or run:  python server.py  to use the web embed instead.")
    except requests.exceptions.HTTPError as exc:
        print(f"API error: {exc}", file=sys.stderr)
        if exc.response is not None:
            print(exc.response.text, file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(
            f"Could not connect to {base_url}. Check your network connection.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Approach B: CLI subprocess (uses confirmed vb commands)
# ---------------------------------------------------------------------------

def start_session_cli() -> None:
    """Start a voice session using the vb CLI."""
    vb_path = shutil.which("vb")
    if vb_path is None:
        print(
            "Error: 'vb' CLI not found. Install it with:\n"
            "  uv pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"=== Agent: {DEFAULT_CONFIG.name} ===\n")

    # Show current agent info
    print("--- Current agent status ---")
    subprocess.run([vb_path, "agent"], check=False)

    # Show current config
    print("\n--- Current configuration ---")
    subprocess.run([vb_path, "config", "show"], check=False)

    # Start debug stream so conversation events are visible
    print("\n--- Starting debug event stream ---")
    print("(Press Ctrl+C to stop)\n")
    try:
        subprocess.run([vb_path, "debug"], check=False)
    except KeyboardInterrupt:
        print("\nDebug stream stopped.")

    # View session logs
    print("\n--- Session logs ---")
    subprocess.run([vb_path, "logs"], check=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    api_key = get_api_key()

    print("Vocal Bridge — Hello World Agent")
    print("=" * 40)
    print()
    print("Choose how to start the session:")
    print("  1) CLI (uses vb commands — requires vb auth login)")
    print("  2) REST API (calls POST /api/v1/token)")
    print()

    choice = input("Enter 1 or 2 [default: 1]: ").strip() or "1"

    if choice == "2":
        start_session_rest_api(api_key)
    else:
        start_session_cli()


if __name__ == "__main__":
    main()
