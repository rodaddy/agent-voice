"""The writer: an OpenAI-compatible LLM decides what the persona says out loud."""

from __future__ import annotations

import re

import httpx

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
TASK = (
    "\n\nYou are the spoken VOICE of a coding/agent assistant. You will be given "
    "the assistant's latest written reply to its user. Say out loud, in "
    "character, the gist of it in one or two short sentences, at most "
    "{max_words} words in total: what happened, what the user needs to know or "
    "decide. Plain spoken words only: no markdown, code, file paths, URLs, "
    "hashes, or long numbers. Never explain that you are summarizing. Output "
    "only the sentences."
)


class Writer:
    """One chat-completions endpoint used to write spoken lines."""

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        api_key: str = "",
        max_words: int = 35,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_words = max_words
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.Client(
            timeout=timeout, headers=headers, transport=transport
        )

    def line_for(
        self, reply: str, persona: str, *, max_reply_chars: int = 4000
    ) -> str | None:
        """Ask the model for the persona's spoken line about ``reply``."""
        system = persona + TASK.format(max_words=self.max_words)
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": reply[:max_reply_chars]},
            ],
            "max_tokens": 160,
            "temperature": 0.8,
            # Thinking models: ask for no thinking; harmless where unsupported.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        r = self._client.post(f"{self.base_url}/v1/chat/completions", json=body)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"] or ""
        return trim_to_sentences(clean(content), self.max_words)


def clean(content: str) -> str:
    """Strip thinking blocks and markdown emphasis, collapse whitespace."""
    return " ".join(THINK_RE.sub("", content).replace("*", "").split())


def trim_to_sentences(text: str, max_words: int) -> str | None:
    """Keep whole sentences up to ``max_words``; never cut mid-sentence."""
    words = text.split()
    if len(words) <= max_words:
        return text or None
    cut = " ".join(words[:max_words])
    end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if end > 0:
        return cut[: end + 1]
    return (cut + ".") if cut else None
