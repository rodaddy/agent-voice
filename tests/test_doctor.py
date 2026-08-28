import json

import httpx
import pytest

from agent_voice import doctor
from agent_voice.config import Config
from agent_voice.doctor import render, run


@pytest.fixture(autouse=True)
def _host_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor, "find_player", lambda: ["/usr/bin/afplay"])
    monkeypatch.setattr("shutil.which", lambda _name: "/usr/bin/ffmpeg")


def _transport(tts_ok: bool, models: list[str]) -> httpx.MockTransport:
    def handle(req: httpx.Request) -> httpx.Response:
        if req.url.path == "/health":
            return httpx.Response(
                200 if tts_ok else 503, json={"status": "ok", "serverType": "OmniVoice"}
            )
        if req.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": m} for m in models]})
        return httpx.Response(404)

    return httpx.MockTransport(handle)


def test_all_good(config: Config) -> None:
    checks = run(config, transport=_transport(True, ["fake"]))
    by = {c.name: c for c in checks}
    assert by["tts"].ok and by["voices"].ok and by["writer"].ok and by["python"].ok
    assert "OmniVoice" in by["tts"].detail
    assert "problem" not in render(checks)


def test_tts_down_and_wrong_model(config: Config) -> None:
    checks = run(config, transport=_transport(False, ["other"]))
    by = {c.name: c for c in checks}
    assert not by["tts"].ok and by["tts"].required and "INSTALL.md" in by["tts"].fix
    assert not by["writer"].ok and not by["writer"].required
    assert "1 problem(s)" in render(checks)


def test_no_voices(config: Config, tmp_path) -> None:  # type: ignore[no-untyped-def]
    cfg = Config(**{**config.__dict__, "voices_dir": tmp_path / "empty", "llm_url": ""})
    by = {c.name: c for c in run(cfg, transport=_transport(True, []))}
    assert not by["voices"].ok and "ref.wav" in by["voices"].fix
    assert by["writer"].ok and not by["writer"].required
    assert json.dumps(by["writer"].detail)  # serializable, sanity


def test_missing_player_is_only_fatal_when_playing(
    config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(doctor, "find_player", lambda: None)
    monkeypatch.setattr("sys.platform", "linux")
    loud = Config(**{**config.__dict__, "play": True})
    playing = {c.name: c for c in run(loud, transport=_transport(True, ["fake"]))}
    assert not playing["player"].ok and playing["player"].required
    silent = Config(**{**config.__dict__, "play": False})
    quiet = {c.name: c for c in run(silent, transport=_transport(True, ["fake"]))}
    assert not quiet["player"].ok and not quiet["player"].required
