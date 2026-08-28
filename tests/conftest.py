import base64
import json
import struct
from pathlib import Path

import httpx
import pytest

from agent_voice.config import Config

WAV = (
    b"RIFF"
    + struct.pack("<I", 36)
    + b"WAVEfmt "
    + struct.pack("<IHHIIHH", 16, 1, 1, 24000, 48000, 2, 16)
    + b"data"
    + struct.pack("<I", 0)
)


@pytest.fixture
def library(tmp_path: Path) -> Path:
    v = tmp_path / "voices" / "alpha"
    v.mkdir(parents=True)
    (v / "ref.wav").write_bytes(WAV)
    (v / "ref.txt").write_text("Hello there.\n")
    (v / "persona.md").write_text("You are Alpha, terse and cheerful.")
    return tmp_path / "voices"


@pytest.fixture
def config(library: Path, tmp_path: Path) -> Config:
    return Config(
        tts_url="http://tts.test",
        voices_dir=library,
        llm_url="http://llm.test",
        llm_model="fake",
        out_dir=tmp_path / "out",
        play=False,
        port=0,
    )


def fake_tts(calls: list[dict]) -> httpx.MockTransport:
    def handle(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "serverType": "OmniVoice"})
        body = json.loads(req.content)
        calls.append(body)
        return httpx.Response(
            200, json={"audio_base64": base64.b64encode(WAV).decode()}
        )

    return httpx.MockTransport(handle)


def fake_llm(reply: str, calls: list[dict]) -> httpx.MockTransport:
    def handle(req: httpx.Request) -> httpx.Response:
        calls.append(json.loads(req.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": reply}}]})

    return httpx.MockTransport(handle)
