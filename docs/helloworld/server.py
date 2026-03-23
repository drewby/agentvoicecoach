#!/usr/bin/env python3
"""
Backend server for the Vocal Bridge web embed.

Serves static files from web_embed/ and exposes a POST /api/session endpoint
that calls the Vocal Bridge API to obtain a LiveKit room token. The frontend
(app.js) uses that token to connect via the LiveKit JS client SDK.

Usage:
    source .venv/bin/activate
    python server.py
    # Open http://localhost:8000
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

STATIC_DIR = Path(__file__).resolve().parent / "web_embed"
PORT = int(os.environ.get("PORT", 8000))


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level}: {msg}")


def log_error(msg: str) -> None:
    log(msg, level="ERROR")


# ---------------------------------------------------------------------------
# API key
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    key = os.environ.get("VB_API_KEY", "")
    if not key or not key.startswith("vb_"):
        log_error(
            "VB_API_KEY is missing or invalid.\n"
            "  1. Copy .env.example to .env\n"
            "  2. Set VB_API_KEY=vb_… with your real key\n"
            "  3. Get a key at https://vocalbridgeai.com/auth/signup"
        )
        sys.exit(1)
    return key


API_KEY = get_api_key()

# Vocal Bridge API — token endpoint
# See: https://vocalbridgeai.com/docs/developer-guide#api-reference
# NOTE: Use https:// — http:// will redirect and strip the POST method (→ 405).
VB_API_URL = os.environ.get("VB_API_URL", "https://vocalbridgeai.com")
VB_TOKEN_ENDPOINT = f"{VB_API_URL}/api/v1/token"


def create_session(participant_name: str = "Web User") -> dict:
    """
    Call the Vocal Bridge token endpoint to get a LiveKit access token.

    POST https://vocalbridgeai.com/api/v1/token
    Headers: X-API-Key: vb_…
    Body: {"participant_name": "Web User"}

    Returns: {"livekit_url": "wss://…", "token": "eyJ…", "room_name": "…"}
    """
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"participant_name": participant_name}

    log(f"POST {VB_TOKEN_ENDPOINT}  participant={participant_name}")

    resp = requests.post(VB_TOKEN_ENDPOINT, json=payload, headers=headers, timeout=30)

    log(f"Vocal Bridge responded: {resp.status_code}")

    if resp.status_code != 200:
        body = resp.text[:500]
        log_error(f"Vocal Bridge API error ({resp.status_code}): {body}")
        resp.raise_for_status()

    data = resp.json()

    log(f"Room: {data.get('room_name')}  Agent mode: {data.get('agent_mode')}  "
        f"Expires in: {data.get('expires_in')}s")

    # Response fields per the API docs:
    #   livekit_url, token, room_name, participant_identity, expires_in, agent_mode
    return {
        "livekit_url": data["livekit_url"],
        "token": data["token"],
        "room_name": data.get("room_name"),
    }


class Handler(SimpleHTTPRequestHandler):
    """Serve static files + the /api/session endpoint."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    # --- API route -----------------------------------------------------------

    def do_POST(self):
        if self.path == "/api/session":
            self._handle_session()
        else:
            log_error(f"POST {self.path} — no handler, returning 404")
            self.send_error(404, "Not found")

    def _handle_session(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            participant_name = body.get("participant_name", "Web User")

            result = create_session(participant_name)

            log(f"Token issued — sending to browser")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except requests.exceptions.ConnectionError as exc:
            msg = f"Could not reach {VB_TOKEN_ENDPOINT} — check your network connection."
            log_error(f"ConnectionError: {exc}")
            log_error(msg)
            self._json_error(502, msg)

        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 502
            detail = exc.response.text[:500] if exc.response is not None else str(exc)

            if status == 405:
                hint = (
                    f"405 Method Not Allowed from Vocal Bridge API. "
                    f"This usually means the URL redirected (http→https) and "
                    f"the POST was converted to GET. Current URL: {VB_TOKEN_ENDPOINT}  "
                    f"Try setting VB_API_URL=https://vocalbridgeai.com in .env"
                )
                log_error(hint)
                self._json_error(502, hint)
            elif status == 403:
                hint = f"403 Forbidden — your API key may be invalid or revoked. Detail: {detail}"
                log_error(hint)
                self._json_error(403, hint)
            else:
                log_error(f"Vocal Bridge API returned {status}: {detail}")
                self._json_error(status, f"Vocal Bridge API error ({status}): {detail}")

        except (ValueError, KeyError) as exc:
            log_error(f"Unexpected response: {exc}")
            self._json_error(500, f"Unexpected API response: {exc}")

    def _json_error(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

    # --- Suppress noisy favicon 404 logs ------------------------------------

    def log_message(self, fmt, *args):
        if len(args) >= 1 and "favicon.ico" in str(args[0]):
            return
        super().log_message(fmt, *args)


def main():
    print("=" * 60)
    print("  Vocal Bridge — Hello World Agent (Web Server)")
    print("=" * 60)
    log(f"Static files: {STATIC_DIR}")
    log(f"Vocal Bridge API: {VB_TOKEN_ENDPOINT}")
    log(f"API key: {API_KEY[:6]}…{'*' * 8}")
    log(f"Listening on http://localhost:{PORT}")
    print()

    server = HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
