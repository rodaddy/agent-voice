import json
import threading
import urllib.request
from collections.abc import Iterator

import pytest

from agent_voice.config import Config
from agent_voice.server import create_server
from agent_voice.speaker import Speaker
from tests.conftest import fake_llm, fake_tts


@pytest.fixture
def url(config: Config) -> Iterator[str]:
    speaker = Speaker(
        config, tts_transport=fake_tts([]), llm_transport=fake_llm("Line.", [])
    )
    server = create_server(config, speaker)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def _post(url: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url + "/say",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_health(url: str) -> None:
    with urllib.request.urlopen(url + "/health") as r:
        data = json.loads(r.read())
    assert (
        data["status"] == "ok"
        and data["voices"] == ["alpha"]
        and data["writer"] is True
    )
    assert data["tts"]["serverType"] == "OmniVoice"


def test_say_routes(url: str) -> None:
    status, data = _post(url, {"text": "x <say>Hi.</say>"})
    assert status == 200 and data["spoken"] == "Hi." and data["source"] == "tag"
    status, data = _post(url, {"text": "plain", "mode": "writer"})
    assert status == 200 and data["source"] == "writer" and data["spoken"] == "Line."
    assert _post(url, {"text": "plain", "mode": "tag"})[0] == 204
    assert _post(url, {"text": "", "mode": "auto"})[0] == 400
    assert _post(url, {"text": "x", "voice": "ghost"})[0] == 404
