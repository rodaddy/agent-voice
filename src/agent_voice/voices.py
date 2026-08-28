"""The voice library: ``voices/<name>/{ref.wav, ref.txt, language.txt, persona.md}``.

``ref.wav`` is a 3-10 s clip of the voice, ``ref.txt`` its exact transcript,
``language.txt`` the spoken language (default English), and ``persona.md``
the optional system prompt a writer LLM uses to decide what this voice says.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_PERSONA = (
    "You are the spoken voice of an AI assistant: warm, direct, a little dry."
)


class VoiceNotFoundError(LookupError):
    """No such voice directory, or it is missing ref.wav / ref.txt."""


@dataclass(frozen=True)
class Voice:
    """One entry in the library."""

    name: str
    ref_audio: Path
    ref_text: str
    language: str = "English"
    persona: str = DEFAULT_PERSONA


def list_voices(voices_dir: Path) -> list[str]:
    """Names of every complete voice under ``voices_dir``, sorted."""
    if not voices_dir.is_dir():
        return []
    return sorted(
        p.name
        for p in voices_dir.iterdir()
        if (p / "ref.wav").is_file() and (p / "ref.txt").is_file()
    )


def load_voice(voices_dir: Path, name: str) -> Voice:
    """Load ``voices_dir/name`` (first voice if ``name`` is empty)."""
    if not name:
        names = list_voices(voices_dir)
        if not names:
            raise VoiceNotFoundError(f"no voices in {voices_dir}")
        name = names[0]
    d = voices_dir / name
    ref_audio, ref_text = d / "ref.wav", d / "ref.txt"
    if not (ref_audio.is_file() and ref_text.is_file()):
        raise VoiceNotFoundError(f"{d} needs ref.wav and ref.txt")
    return Voice(
        name=name,
        ref_audio=ref_audio,
        ref_text=ref_text.read_text(encoding="utf-8").strip(),
        language=_read(d / "language.txt", "English"),
        persona=_read(d / "persona.md", DEFAULT_PERSONA),
    )


def _read(path: Path, default: str) -> str:
    return path.read_text(encoding="utf-8").strip() if path.is_file() else default
