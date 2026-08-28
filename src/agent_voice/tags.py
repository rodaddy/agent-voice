"""The ``<say>...</say>`` channel: an agent marks the one line meant to be spoken."""

from __future__ import annotations

import re

SAY_RE = re.compile(r"<say>(.*?)</say>", re.DOTALL | re.IGNORECASE)
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


def spoken_line(text: str, max_chars: int = 300) -> str | None:
    """The last ``<say>`` line in ``text``, ignoring tags quoted in code spans."""
    found = SAY_RE.findall(CODE_RE.sub("", text))
    if not found:
        return None
    line = " ".join(found[-1].split())[:max_chars]
    return line or None


def strip_markup(text: str) -> str:
    """Drop code spans and markdown emphasis; collapse whitespace."""
    plain = CODE_RE.sub("", text).replace("*", "").replace("#", "")
    return " ".join(plain.split())
