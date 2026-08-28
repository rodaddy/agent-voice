"""``agent-voice serve``: a tiny HTTP front so any agent, in any language, can talk.

    POST /say    {"text": "...", "voice": "name", "mode": "auto|tag|writer|direct"}
                 -> {"spoken": "...", "wav": "...", "voice": "name", "source": "tag"}
                 -> 204 when there was nothing to say
    GET  /health -> {"status": "ok", "voices": [...], "writer": bool, "tts": {...}}

Standard library only; utterances are serialized by the Speaker's lock.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast

from agent_voice.config import Config
from agent_voice.speaker import Mode, Speaker
from agent_voice.voices import VoiceNotFoundError

MODES = ("auto", "tag", "writer", "direct")


def create_server(
    config: Config, speaker: Speaker | None = None
) -> ThreadingHTTPServer:
    """Build the server (call ``serve_forever()`` on it)."""
    spk = speaker or Speaker(config)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D102
            return

        def _send(self, status: HTTPStatus, body: dict[str, Any] | None = None) -> None:
            data = json.dumps(body).encode() if body is not None else b""
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: D102, N802
            if self.path != "/health":
                self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            self._send(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "voices": spk.voices(),
                    "writer": spk.writer is not None,
                    "tts": spk.tts.health(),
                },
            )

        def do_POST(self) -> None:  # noqa: D102, N802
            if self.path != "/say":
                self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length") or 0)
            try:
                req = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})
                return
            text = str(req.get("text") or "")
            mode = str(req.get("mode") or "auto")
            if not text or mode not in MODES:
                msg = "need text; mode in " + "|".join(MODES)
                self._send(HTTPStatus.BAD_REQUEST, {"error": msg})
                return
            try:
                spoken = spk.speak(text, str(req.get("voice") or ""), cast(Mode, mode))
            except VoiceNotFoundError as exc:
                self._send(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                return
            except Exception as exc:  # noqa: BLE001 -- report, never crash the server
                self._send(
                    HTTPStatus.BAD_GATEWAY, {"error": f"{type(exc).__name__}: {exc}"}
                )
                return
            if spoken is None:
                self._send(HTTPStatus.NO_CONTENT)
                return
            self._send(
                HTTPStatus.OK,
                {
                    "spoken": spoken.text,
                    "wav": str(spoken.wav),
                    "voice": spoken.voice,
                    "source": spoken.source,
                },
            )

    return ThreadingHTTPServer((config.host, config.port), Handler)
