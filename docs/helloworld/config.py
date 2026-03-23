"""
Vocal Bridge agent configuration constants.

All known configurable parameters for a Vocal Bridge voice agent.
"""

from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for a Vocal Bridge voice agent."""

    # --- Agent identity ---
    name: str = "Hello World Agent"
    style: str = "Chatty"
    prompt: str = (
        "You are a friendly greeting assistant. When someone speaks to you, "
        "warmly greet them, ask how their day is going, and have a brief "
        "pleasant conversation. Keep responses concise and natural. "
        "When the user asks for something to be written down, summarized "
        "as text, or exported as a document, use the send_document action "
        "to deliver it to their screen instead of reading it aloud. "
        "When the conversation reaches a natural end (the user says goodbye, "
        "thanks you, or you've completed their request), use the "
        "end_conversation action to close the session."
    )

    # --- Runtime settings ---
    max_call_duration: int = 5        # minutes
    max_history_messages: int = 10    # context window size
    debug_mode: bool = True

    # --- Voice / TTS (select from available options in the dashboard) ---
    # TODO: Check vocalbridgeai.com/docs/developer-guide for available
    #       voice and TTS model options after signing up.
    voice: str | None = None          # e.g. a voice ID or name
    tts_model: str | None = None      # e.g. a TTS model identifier


# Default configuration used by setup_agent.py and run_agent.py
DEFAULT_CONFIG = AgentConfig()
