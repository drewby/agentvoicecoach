"""
VoiceCoach agent configurations.

Defines settings for both the Simulation Agent (AI customer)
and the Coaching Agent (transcript evaluator).
"""

from dataclasses import dataclass
from pathlib import Path


AGENTS_DIR = Path(__file__).parent


@dataclass
class SimulationAgentConfig:
    """Configuration for the Simulation Agent (AI customer persona)."""

    name: str = "VoiceCoach Customer"
    style: str = "Conversational"
    prompt_file: str = "simulation_prompt.md"
    max_call_duration: int = 10       # minutes
    max_history_messages: int = 20    # context window size
    debug_mode: bool = True

    @property
    def prompt_path(self) -> Path:
        return AGENTS_DIR / self.prompt_file

    @property
    def client_actions_path(self) -> Path:
        return AGENTS_DIR / "client_actions_sim.json"

    @property
    def scenarios_path(self) -> Path:
        return AGENTS_DIR / "scenarios.json"


@dataclass
class CoachingAgentConfig:
    """Configuration for the Coaching Agent (transcript evaluator)."""

    name: str = "VoiceCoach Coach"
    style: str = "Professional"
    prompt_file: str = "coaching_prompt.md"
    max_call_duration: int = 5        # minutes
    max_history_messages: int = 10    # context window size
    debug_mode: bool = True

    @property
    def prompt_path(self) -> Path:
        return AGENTS_DIR / self.prompt_file

    @property
    def client_actions_path(self) -> Path:
        return AGENTS_DIR / "client_actions_coach.json"


# Default configurations
SIMULATION_CONFIG = SimulationAgentConfig()
COACHING_CONFIG = CoachingAgentConfig()
