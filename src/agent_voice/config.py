"""Configuration from ``AGENT_VOICE_*`` environment variables.

``agent-voice.env`` in the current directory (``KEY=VALUE`` lines, optional
``export``, ``#`` comments) is read first; real environment variables win.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

PREFIX = "AGENT_VOICE_"
ENV_FILE = Path("agent-voice.env")


@dataclass(frozen=True)
class Config:
    """Every knob; the environment variable that sets it is in the comment."""

    tts_url: str = "http://127.0.0.1:8181"  # AGENT_VOICE_TTS_URL
    voices_dir: Path = Path("voices")  # AGENT_VOICE_VOICES_DIR
    voice: str = ""  # AGENT_VOICE_VOICE (default: first voice in the library)
    llm_url: str = ""  # AGENT_VOICE_LLM_URL (OpenAI-compatible base; "" = no writer)
    llm_model: str = ""  # AGENT_VOICE_LLM_MODEL
    llm_api_key: str = ""  # AGENT_VOICE_LLM_API_KEY
    num_steps: int = 10  # AGENT_VOICE_NUM_STEPS (OmniVoice diffusion steps)
    guidance_scale: float = 1.2  # AGENT_VOICE_GUIDANCE_SCALE
    max_words: int = 35  # AGENT_VOICE_MAX_WORDS (cap on a writer-produced line)
    out_dir: Path = Path("out")  # AGENT_VOICE_OUT_DIR (where WAVs are saved)
    play: bool = True  # AGENT_VOICE_PLAY (0/false to only save the WAV)
    host: str = "127.0.0.1"  # AGENT_VOICE_HOST (agent-voice serve)
    port: int = 7161  # AGENT_VOICE_PORT

    @classmethod
    def from_env(
        cls, env: Mapping[str, str] | None = None, env_file: Path | None = ENV_FILE
    ) -> Config:
        """Build a config from ``env_file`` then ``env`` (default ``os.environ``)."""
        source: dict[str, str] = {}
        if env_file is not None and env_file.is_file():
            source.update(read_env_file(env_file))
        source.update(os.environ if env is None else env)
        cfg = cls()
        values: dict[str, Any] = {}
        for f in fields(cls):
            raw = source.get(PREFIX + f.name.upper())
            if raw is not None:
                values[f.name] = _coerce(getattr(cfg, f.name), raw)
        return replace(cfg, **values)

    @property
    def has_writer(self) -> bool:
        """True when a writer LLM is configured."""
        return bool(self.llm_url and self.llm_model)


def _coerce(current: object, raw: str) -> object:
    if isinstance(current, Path):
        return Path(raw).expanduser()
    if isinstance(current, bool):
        return raw.strip().lower() not in {"0", "false", "no", "off", ""}
    if isinstance(current, int):
        return int(raw)
    if isinstance(current, float):
        return float(raw)
    return raw


def read_env_file(path: Path) -> dict[str, str]:
    """Parse ``KEY=VALUE`` lines (``export`` prefix, quotes, ``#`` comments ok)."""
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values
