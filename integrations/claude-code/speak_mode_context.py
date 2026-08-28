"""Claude Code UserPromptSubmit hook: tell the model what speak mode expects."""

from __future__ import annotations

import os
import sys
from pathlib import Path

FLAG = Path.home() / ".agent-voice" / "speak-mode"


def main() -> int:
    """Print the instruction while the flag exists; otherwise nothing."""
    if not FLAG.is_file():
        return 0
    voice = FLAG.read_text(encoding="utf-8").strip() or "the default voice"
    if os.environ.get("AGENT_VOICE_LLM_URL"):
        print(
            "Speak mode is ON with a background writer model that turns each "
            "finished reply into the spoken line. Do NOT add <say> tags; reply "
            "normally."
        )
        return 0
    print(
        f"Speak mode is ON. End every reply with exactly one spoken line wrapped "
        f"as <say>...</say>: one or two short sentences, in character for "
        f"'{voice}', plain words only (no markdown, code, paths, URLs, or long "
        "numbers). Only that line is spoken; the rest is shown as usual."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
