"""``agent-voice doctor``: say exactly what is missing, and how to fix it."""

from __future__ import annotations

import shutil
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

import httpx

from agent_voice.config import Config
from agent_voice.play import find_player
from agent_voice.tts import TTS
from agent_voice.voices import list_voices

MAX_REF_SECONDS = 12.0


@dataclass(frozen=True)
class Check:
    """One line of the report."""

    name: str
    ok: bool
    detail: str
    fix: str = ""
    required: bool = True

    @property
    def mark(self) -> str:
        """``ok`` / ``FAIL`` / ``warn`` for the printed report."""
        if self.ok:
            return "ok  "
        return "FAIL" if self.required else "warn"


def run(config: Config, *, transport: httpx.BaseTransport | None = None) -> list[Check]:
    """Run every check and return the report."""
    return [
        _python(),
        _player(),
        _tts(config, transport),
        *_voices(config),
        _writer(config, transport),
        _ffmpeg(),
    ]


def _python() -> Check:
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 11)
    return Check(
        "python", ok, f"{v.major}.{v.minor}.{v.micro}", "agent-voice needs Python 3.11+"
    )


def _player() -> Check:
    if sys.platform == "win32":
        return Check("player", True, "winsound (built in)")
    argv = find_player()
    if argv:
        return Check("player", True, Path(argv[0]).name)
    return Check(
        "player",
        False,
        "no afplay / paplay / aplay / ffplay on PATH",
        "install ffmpeg (ffplay) or pulseaudio-utils (paplay); "
        "or set AGENT_VOICE_PLAY=false",
    )


def _tts(config: Config, transport: httpx.BaseTransport | None) -> Check:
    health = TTS(config.tts_url, transport=transport).health()
    if health:
        kind = health.get("serverType") or health.get("status") or "up"
        return Check("tts", True, f"{config.tts_url} ({kind})")
    return Check(
        "tts",
        False,
        f"{config.tts_url} not answering GET /health",
        "start an OmniVoice server (INSTALL.md step 2) or set AGENT_VOICE_TTS_URL",
    )


def _voices(config: Config) -> list[Check]:
    names = list_voices(config.voices_dir)
    if not names:
        return [
            Check(
                "voices",
                False,
                f"no voices in {config.voices_dir}",
                "add voices/<name>/ref.wav + ref.txt (INSTALL.md step 3) "
                "or set AGENT_VOICE_VOICES_DIR",
            )
        ]
    checks = [Check("voices", True, ", ".join(names))]
    for name in names:
        seconds = _wav_seconds(config.voices_dir / name / "ref.wav")
        if seconds is None:
            checks.append(
                Check(
                    f"voice {name}",
                    False,
                    "ref.wav is not a PCM WAV",
                    "re-export it: "
                    "ffmpeg -i in -ac 1 -ar 24000 -sample_fmt s16 ref.wav",
                )
            )
        elif seconds > MAX_REF_SECONDS:
            checks.append(
                Check(
                    f"voice {name}",
                    False,
                    f"ref.wav is {seconds:.1f} s",
                    "cut it to 3-10 s; long clips are slower and no better",
                    required=False,
                )
            )
    return checks


def _wav_seconds(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate() or 1)
    except (wave.Error, EOFError, OSError):
        return None


def _writer(config: Config, transport: httpx.BaseTransport | None) -> Check:
    if not config.has_writer:
        hint = (
            "optional: set AGENT_VOICE_LLM_URL + AGENT_VOICE_LLM_MODEL "
            "for persona lines"
        )
        return Check(
            "writer",
            True,
            "not configured (tag or direct speech only)",
            hint,
            required=False,
        )
    headers = (
        {"Authorization": f"Bearer {config.llm_api_key}"} if config.llm_api_key else {}
    )
    try:
        with httpx.Client(timeout=5.0, transport=transport, headers=headers) as client:
            r = client.get(f"{config.llm_url.rstrip('/')}/v1/models")
            r.raise_for_status()
            ids = [m.get("id") for m in r.json().get("data", [])]
    except (httpx.HTTPError, ValueError) as exc:
        return Check(
            "writer",
            False,
            f"{config.llm_url}: {type(exc).__name__}",
            "check AGENT_VOICE_LLM_URL / _API_KEY; "
            "the server must speak the OpenAI API",
        )
    if ids and config.llm_model not in ids:
        return Check(
            "writer",
            False,
            f"{config.llm_model} not in /v1/models "
            f"({', '.join(str(i) for i in ids[:6])}...)",
            "set AGENT_VOICE_LLM_MODEL to one of the listed ids",
            required=False,
        )
    return Check("writer", True, f"{config.llm_model} @ {config.llm_url}")


def _ffmpeg() -> Check:
    if shutil.which("ffmpeg"):
        return Check("ffmpeg", True, "found (for making voices)", required=False)
    return Check(
        "ffmpeg",
        False,
        "not found",
        "only needed to cut reference clips: brew/apt install ffmpeg",
        required=False,
    )


def render(checks: list[Check]) -> str:
    """The printed report."""
    lines = []
    for c in checks:
        lines.append(f"[{c.mark}] {c.name:<14} {c.detail}")
        if not c.ok and c.fix:
            lines.append(f"       fix: {c.fix}")
        elif c.ok and not c.required and c.fix:
            lines.append(f"       {c.fix}")
    failed = [c for c in checks if not c.ok and c.required]
    lines.append(
        ""
        if not failed
        else f"{len(failed)} problem(s) to fix before agent-voice can speak."
    )
    return "\n".join(lines).rstrip()
