"""Client for the OmniVoice REST contract (``/health`` + ``/synthesize``).

The contract is the one used by scorbo2's ``server_omnivoice.py`` and
TalkWithMe: POST ``/synthesize`` with the reference clip as base64 WAV and its
transcript, get the synthesized WAV back as base64.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from agent_voice.voices import Voice


class TTS:
    """One TTS server."""

    def __init__(
        self,
        base_url: str,
        *,
        num_steps: int = 10,
        guidance_scale: float = 1.2,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.num_steps = num_steps
        self.guidance_scale = guidance_scale
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def health(self) -> dict[str, Any] | None:
        """``GET /health`` as a dict, or None if the server is unreachable."""
        try:
            r = self._client.get(f"{self.base_url}/health", timeout=5.0)
            r.raise_for_status()
            data: dict[str, Any] = r.json()
        except (httpx.HTTPError, ValueError):
            return None
        return data

    def synthesize(self, text: str, voice: Voice) -> bytes:
        """Return ``text`` spoken in ``voice`` as WAV bytes."""
        body = {
            "text": text,
            "audio_base64": base64.b64encode(voice.ref_audio.read_bytes()).decode(),
            "prompt_text": voice.ref_text,
            "language": voice.language,
            "num_steps": self.num_steps,
            "guidance_scale": self.guidance_scale,
        }
        r = self._client.post(f"{self.base_url}/synthesize", json=body)
        r.raise_for_status()
        return base64.b64decode(r.json()["audio_base64"])
