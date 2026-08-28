# Changelog

## Unreleased

## 0.1.0 — 2026-08-27

First public release.

- `agent-voice speak | pipe | serve | voices | health | doctor`.
- Spoken-line cascade: `<say>...</say>` tag (tags in code spans ignored) →
  writer LLM with the voice's `persona.md` → direct text, markup stripped.
- OmniVoice `/health` + `/synthesize` client, compatible with scorbo2's
  `server_omnivoice.py` and TalkWithMe.
- Voice library: `voices/<name>/{ref.wav, ref.txt, language.txt, persona.md}`.
- Standard-library HTTP server (`POST /say`, `GET /health`), utterances
  serialized.
- Playback via afplay / winsound / paplay / aplay / ffplay.
- Config from `AGENT_VOICE_*` environment variables or `agent-voice.env`.
- `install.sh`, `INSTALL.md`, `agent-voice doctor` with a fix for every failure.
- Example integration: Claude Code hooks.
