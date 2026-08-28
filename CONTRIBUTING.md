# Contributing

Thanks for looking. This is a small tool and it wants to stay small: one
dependency, standard-library HTTP, no framework. Things that fit: new
integrations under `integrations/`, more playback backends, better voice
tooling, doc fixes, bug fixes with a test.

## Setup

```sh
sh install.sh --dev
.venv/bin/pytest
.venv/bin/ruff check && .venv/bin/ruff format --check
.venv/bin/mypy
```

All four must pass; CI runs them on Linux and macOS, Python 3.11–3.13.

## Ground rules

- **Tests use fake transports, never a real server.** See `tests/conftest.py`
  (`fake_tts`, `fake_llm`). A test that needs a running OmniVoice server will
  not be merged.
- **Don't add dependencies** without a reason the README can state in one
  line. `httpx` is the only one.
- **Type everything.** `mypy --strict` is on for `src/`.
- **Keep the TTS contract compatible** with scorbo2's `server_omnivoice.py`
  (`/health`, `/synthesize`); that is why existing servers work unchanged.
- **Don't commit voices.** `voices/` is git-ignored; reference clips are
  usually somebody's copyrighted audio. Examples generate their own.

## Pull requests

One change per PR, with a test when behaviour changes, and a line in
`CHANGELOG.md` under *Unreleased*. Say what you ran; "tests pass" means you
ran them.

## Reporting a problem

Paste the output of `agent-voice doctor` and the exact command. If it is about
synthesis quality, say which server (and GPU/MPS) and how long `ref.wav` is.
