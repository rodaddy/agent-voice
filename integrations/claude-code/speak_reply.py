"""Claude Code Stop hook: feed the finished reply to ``agent-voice pipe``."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FLAG = Path.home() / ".agent-voice" / "speak-mode"
LAST = Path.home() / ".agent-voice" / "speak-mode.last"
LOG = Path.home() / ".agent-voice" / "speak-mode.log"


def last_text_block(transcript: Path) -> str:
    """The final assistant text block in the transcript (the reply's tail)."""
    last = ""
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = entry.get("message", {}).get("content")
        if entry.get("type") != "assistant" or not isinstance(content, list):
            continue
        texts = [b.get("text", "") for b in content if b.get("type") == "text"]
        if texts:
            last = texts[-1]
    return last


def main() -> int:
    """Always exit 0 so the hook can never block the session."""
    if not FLAG.is_file():
        return 0
    voice = FLAG.read_text(encoding="utf-8").strip()
    payload = json.load(sys.stdin)
    transcript = Path(payload.get("transcript_path", ""))
    if not transcript.is_file():
        return 0
    reply = last_text_block(transcript).strip()
    if not reply or (LAST.is_file() and LAST.read_text(encoding="utf-8") == reply):
        return 0
    LAST.parent.mkdir(parents=True, exist_ok=True)
    LAST.write_text(reply, encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "agent_voice", "pipe", "--voice", voice],
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
        assert proc.stdin is not None
        proc.stdin.write(reply.encode("utf-8"))
        proc.stdin.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
