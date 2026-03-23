#!/usr/bin/env python3
"""
Create and configure a Vocal Bridge voice agent using the vb CLI.

Prerequisites:
  1. uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
  2. vb auth login
"""

import shutil
import subprocess
import sys

from config import DEFAULT_CONFIG


def run_vb(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a vb CLI command and return the result."""
    vb_path = shutil.which("vb")
    if vb_path is None:
        print(
            "Error: 'vb' CLI not found. Install it with:\n"
            "  uv pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = [vb_path, *args]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(f"Command failed (exit {result.returncode}):", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    return result


def create_agent() -> None:
    """Create the Hello World agent."""
    cfg = DEFAULT_CONFIG
    print(f"\n=== Creating agent: {cfg.name} ===\n")
    run_vb(
        "create",
        "--name", cfg.name,
        "--style", cfg.style,
        "--prompt", cfg.prompt,
    )


def configure_agent() -> None:
    """Apply runtime configuration to the agent."""
    cfg = DEFAULT_CONFIG
    print("\n=== Configuring agent settings ===\n")

    run_vb("config", "set", "--max-call-duration", str(cfg.max_call_duration))
    run_vb("config", "set", "--max-history-messages", str(cfg.max_history_messages))
    run_vb("config", "set", "--debug-mode", str(cfg.debug_mode).lower())


def configure_client_actions() -> None:
    """Register client actions so the agent can send documents to the UI."""
    import json
    from pathlib import Path

    actions_file = Path(__file__).resolve().parent / "client_actions.json"
    if not actions_file.exists():
        print("Warning: client_actions.json not found, skipping.", file=sys.stderr)
        return

    print("\n=== Configuring client actions ===\n")
    print(f"Loading: {actions_file}")
    actions = json.loads(actions_file.read_text())
    for action in actions:
        print(f"  • {action['name']} ({action['direction']})")

    run_vb("config", "set", "--client-actions-file", str(actions_file))


def main() -> None:
    create_agent()
    configure_agent()
    configure_client_actions()

    print("\n=== Setup complete ===")
    print("Verify your agent with:  vb agent")
    print("View all settings with:  vb config show")


if __name__ == "__main__":
    main()
