"""CLI: ``agent-voice speak | pipe | serve | voices | health``."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from dataclasses import replace
from typing import cast

from agent_voice.config import Config
from agent_voice.speaker import Mode, Speaker
from agent_voice.voices import VoiceNotFoundError


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    args = _parser().parse_args(argv)
    config = Config.from_env()
    if args.no_play:
        config = replace(config, play=False)
    speaker = Speaker(config)
    try:
        return int(args.func(speaker, args))
    except VoiceNotFoundError as exc:
        print(f"agent-voice: {exc}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent-voice", description=__doc__)
    p.add_argument(
        "--no-play", action="store_true", help="save the WAV, do not play it"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("speak", help="speak the given text as-is")
    sp.add_argument("text")
    sp.add_argument("--voice", default="")
    sp.set_defaults(func=_speak)

    pp = sub.add_parser("pipe", help="read an agent reply on stdin, speak its line")
    pp.add_argument("--voice", default="")
    pp.add_argument(
        "--mode", choices=["auto", "tag", "writer", "direct"], default="auto"
    )
    pp.set_defaults(func=_pipe)

    sv = sub.add_parser("serve", help="HTTP front: POST /say, GET /health")
    sv.set_defaults(func=_serve)

    sub.add_parser("voices", help="list the voice library").set_defaults(func=_voices)
    sub.add_parser("health", help="check the TTS server and library").set_defaults(
        func=_health
    )
    return p


def _speak(speaker: Speaker, args: argparse.Namespace) -> int:
    spoken = speaker.speak(args.text, args.voice, "direct")
    print(spoken.wav if spoken else "(nothing to say)")
    return 0


def _pipe(speaker: Speaker, args: argparse.Namespace) -> int:
    text = sys.stdin.read()
    spoken = speaker.speak(text, args.voice, cast(Mode, args.mode))
    if spoken:
        print(f"[{spoken.source}] {spoken.text}")
    return 0


def _serve(speaker: Speaker, _args: argparse.Namespace) -> int:
    from agent_voice.server import create_server

    server = create_server(speaker.config, speaker)
    print(f"agent-voice serving on http://{speaker.config.host}:{speaker.config.port}")
    with contextlib.suppress(KeyboardInterrupt):
        server.serve_forever()
    return 0


def _voices(speaker: Speaker, _args: argparse.Namespace) -> int:
    names = speaker.voices()
    print("\n".join(names) if names else f"(no voices in {speaker.config.voices_dir})")
    return 0


def _health(speaker: Speaker, _args: argparse.Namespace) -> int:
    tts = speaker.tts.health()
    report = {
        "tts": tts,
        "voices": speaker.voices(),
        "writer": speaker.writer is not None,
    }
    print(json.dumps(report, indent=2))
    return 0 if tts else 1


if __name__ == "__main__":
    sys.exit(main())
