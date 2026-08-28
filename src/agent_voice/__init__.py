"""agent-voice: give any LLM agent a cloned voice.

Text goes in (a whole agent reply, or one line tagged ``<say>...</say>``),
a persona decides what is worth saying out loud, an OmniVoice-style TTS
server clones the voice, and the audio plays. No agent framework required:
a CLI, a stdin pipe, and a tiny HTTP server cover every runtime.
"""

from agent_voice.config import Config
from agent_voice.speaker import Speaker, Spoken

__all__ = ["Config", "Speaker", "Spoken"]
__version__ = "0.1.0"
