#!/usr/bin/env python3
"""
Create and configure VoiceCoach agents using the vb CLI.

Creates two agents:
  1. Simulation Agent — the AI customer persona for training scenarios
  2. Coaching Agent — the transcript evaluator that scores performance

Prerequisites:
  1. pip install -r requirements.txt
  2. vb auth login
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from config import SIMULATION_CONFIG, COACHING_CONFIG


def run_vb(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a vb CLI command and return the result."""
    vb_path = shutil.which("vb")
    if vb_path is None:
        print(
            "Error: 'vb' CLI not found. Install it with:\n"
            "  pip install vocal-bridge",
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
    return result


def create_agent(name: str, style: str, prompt_path: Path) -> None:
    """Create a single agent via vb CLI. Idempotent — skips if exists."""
    print(f"\n=== Creating agent: {name} ===\n")
    prompt_text = prompt_path.read_text() if prompt_path.exists() else ""
    result = run_vb("create", "--name", name, "--style", style, "--prompt", prompt_text)
    if result.returncode != 0:
        print(f"  (Agent '{name}' may already exist — continuing)")


def configure_agent(name: str, max_duration: int, max_history: int, debug: bool) -> None:
    """Apply runtime settings to agent."""
    print(f"\n=== Configuring {name} ===\n")
    run_vb("config", "set", "--max-call-duration", str(max_duration))
    run_vb("config", "set", "--max-history-messages", str(max_history))
    run_vb("config", "set", "--debug-mode", str(debug).lower())


def register_client_actions(actions_path: Path) -> None:
    """Register client actions from a JSON file."""
    if not actions_path.exists():
        print(f"  Warning: {actions_path.name} not found, skipping.")
        return

    print(f"\n=== Registering client actions: {actions_path.name} ===\n")
    actions = json.loads(actions_path.read_text())
    for action in actions:
        print(f"  • {action['name']} ({action['direction']})")
    run_vb("config", "set", "--client-actions-file", str(actions_path))


def setup_simulation_agent() -> None:
    """Set up the Simulation Agent (AI customer)."""
    cfg = SIMULATION_CONFIG
    create_agent(cfg.name, cfg.style, cfg.prompt_path)
    configure_agent(cfg.name, cfg.max_call_duration, cfg.max_history_messages, cfg.debug_mode)
    register_client_actions(cfg.client_actions_path)


def setup_coaching_agent() -> None:
    """Set up the Coaching Agent (transcript evaluator)."""
    cfg = COACHING_CONFIG
    create_agent(cfg.name, cfg.style, cfg.prompt_path)
    configure_agent(cfg.name, cfg.max_call_duration, cfg.max_history_messages, cfg.debug_mode)
    register_client_actions(cfg.client_actions_path)


def main() -> None:
    setup_simulation_agent()
    setup_coaching_agent()

    print("\n=== Setup complete ===")
    print("Verify agents with:  vb agent")
    print("View settings with:  vb config show")


if __name__ == "__main__":
    main()
