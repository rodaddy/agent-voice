"""The Speaker: text in, persona line chosen, voice synthesized, audio played."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import httpx

from agent_voice.config import Config
from agent_voice.play import play
from agent_voice.tags import spoken_line, strip_markup
from agent_voice.tts import TTS
from agent_voice.voices import Voice, list_voices, load_voice
from agent_voice.writer import Writer

Mode = Literal["auto", "tag", "writer", "direct"]
DIRECT_MAX_CHARS = 600


@dataclass(frozen=True)
class Spoken:
    """What was said and where the audio went."""

    text: str
    wav: Path
    voice: str
    source: str  # "tag" | "writer" | "direct"


class Speaker:
    """Chooses the line, synthesizes it, and plays it -- one utterance at a time."""

    def __init__(
        self,
        config: Config,
        *,
        tts_transport: httpx.BaseTransport | None = None,
        llm_transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config
        self.tts = TTS(
            config.tts_url,
            num_steps=config.num_steps,
            guidance_scale=config.guidance_scale,
            transport=tts_transport,
        )
        self.writer = (
            Writer(
                config.llm_url,
                config.llm_model,
                api_key=config.llm_api_key,
                max_words=config.max_words,
                transport=llm_transport,
            )
            if config.has_writer
            else None
        )
        self._lock = threading.Lock()  # never talk over yourself

    def voices(self) -> list[str]:
        """Names in the library."""
        return list_voices(self.config.voices_dir)

    def choose(
        self, text: str, voice: Voice, mode: Mode = "auto"
    ) -> tuple[str, str] | None:
        """Pick the line to speak: ``(line, source)`` or None for silence."""
        tagged = spoken_line(text)
        if mode in ("auto", "tag") and tagged:
            return tagged, "tag"
        if mode == "tag":
            return None
        if mode in ("auto", "writer") and self.writer is not None:
            line = self.writer.line_for(text, voice.persona)
            return (line, "writer") if line else None
        if mode == "writer":
            return None
        plain = strip_markup(text)[:DIRECT_MAX_CHARS]
        return (plain, "direct") if plain else None

    def speak(
        self,
        text: str,
        voice_name: str = "",
        mode: Mode = "auto",
        *,
        play_audio: bool | None = None,
    ) -> Spoken | None:
        """Speak ``text`` (per ``mode``) in ``voice_name``; return what was said."""
        voice = load_voice(self.config.voices_dir, voice_name or self.config.voice)
        chosen = self.choose(text, voice, mode)
        if chosen is None:
            return None
        line, source = chosen
        with self._lock:
            wav = self.tts.synthesize(line, voice)
            path = self._save(wav, voice.name)
            if self.config.play if play_audio is None else play_audio:
                play(path)
        return Spoken(text=line, wav=path, voice=voice.name, source=source)

    def _save(self, wav: bytes, voice: str) -> Path:
        self.config.out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
        path = self.config.out_dir / f"{voice}-{stamp}.wav"
        path.write_bytes(wav)
        return path
