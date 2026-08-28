"""Play a WAV with whatever the host has: afplay, winsound, paplay, aplay, ffplay."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CANDIDATES: tuple[tuple[str, list[str]], ...] = (
    ("afplay", []),
    ("paplay", []),
    ("aplay", ["-q"]),
    ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
)


def find_player() -> list[str] | None:
    """The playback argv prefix for this host, or None if nothing is installed."""
    for name, extra in CANDIDATES:
        exe = shutil.which(name)
        if exe:
            return [exe, *extra]
    return None


def play(path: Path) -> bool:
    """Play ``path`` synchronously; return False if no player is available."""
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(str(path), winsound.SND_FILENAME)
        return True
    argv = find_player()
    if argv is None:
        return False
    subprocess.run([*argv, str(path)], check=False)
    return True
