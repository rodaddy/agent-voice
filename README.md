# agent-voice

Give any LLM agent a cloned voice. Text goes in — a whole reply, or one line
the agent tagged `<say>...</say>` — a persona decides what is worth saying out
loud, an [OmniVoice](https://github.com/k2-fsa/OmniVoice)-style TTS server
clones the voice, and the audio plays on the box you're sitting at.

No framework required. Three doors, so it fits whatever your agents run in:

```sh
agent-voice speak "Build is green."                 # say exactly this
my-agent --reply | agent-voice pipe --voice skippy   # speak the agent's reply
agent-voice serve                                    # POST /say from anything, in any language
```

It grew out of a Claude Code session that wanted to talk as
[Skippy](https://expeditionaryforce.fandom.com/wiki/Skippy) without hauling a
browser around. The TTS contract is the one from scorbo2's
[server_omnivoice.py](https://github.com/scorbo2/ai-playground/tree/master/TTS)
and [TalkWithMe](https://github.com/scorbo2/TalkWithMe), so an existing server
from either works unchanged.

## How a line gets chosen

`agent-voice pipe` and `POST /say` take a whole reply and pick what to say:

1. **`<say>` tag** — if the agent wrote `<say>One spoken line.</say>`, that line
   is spoken and nothing else. Tags quoted inside code spans are ignored. This
   is the "two channels" pattern: the screen gets the technical reply, the
   speaker gets the persona's one-liner.
2. **Writer LLM** — otherwise, if `AGENT_VOICE_LLM_URL` is set, the reply is
   sent to that (OpenAI-compatible) model with the voice's `persona.md` and it
   answers with one or two spoken sentences in character (capped at
   `AGENT_VOICE_MAX_WORDS`, never cut mid-sentence). A small local model is
   plenty; a 9B does it in ~2.5 s.
3. **Direct** — otherwise the text itself is spoken, markup stripped.

`--mode tag|writer|direct` forces one of these; `auto` is the cascade above.

## Install

```sh
pip install -e .          # from a checkout; Python 3.11+, one dependency (httpx)
```

Playback uses whatever the host has: `afplay` (macOS), `winsound` (Windows),
`paplay` / `aplay` / `ffplay` (Linux).

You also need an OmniVoice server. The quickest is scorbo2's
[`server_omnivoice.py`](https://github.com/scorbo2/ai-playground/tree/master/TTS);
any server exposing `GET /health` and `POST /synthesize` with the same JSON
works.

## Voices

A voice is a directory:

```
voices/skippy/
  ref.wav        3-10 s of the voice, mono, 24 kHz (longer does not help and is slower)
  ref.txt        the exact words spoken in ref.wav
  language.txt   optional, default "English"
  persona.md     optional: the system prompt the writer LLM speaks with
```

`examples/make-voice-macos.sh voices/demo` builds a throwaway voice from the
macOS `say` command so you can try the pipeline before you have a real clip.
`examples/persona-ship-ai.md` is a starting persona.

## Configuration

Everything is an `AGENT_VOICE_*` environment variable (see `config.py`):

| Variable | Default | Meaning |
|---|---|---|
| `AGENT_VOICE_TTS_URL` | `http://127.0.0.1:8000` | OmniVoice server |
| `AGENT_VOICE_VOICES_DIR` | `voices` | the library |
| `AGENT_VOICE_VOICE` | first voice | default voice name |
| `AGENT_VOICE_LLM_URL` | (unset) | OpenAI-compatible base URL of the writer; unset = no writer |
| `AGENT_VOICE_LLM_MODEL` | | writer model id |
| `AGENT_VOICE_LLM_API_KEY` | | sent as `Authorization: Bearer` if set |
| `AGENT_VOICE_NUM_STEPS` | `10` | OmniVoice diffusion steps |
| `AGENT_VOICE_GUIDANCE_SCALE` | `1.2` | |
| `AGENT_VOICE_MAX_WORDS` | `35` | cap on a writer-produced line |
| `AGENT_VOICE_OUT_DIR` | `out` | where WAVs are saved |
| `AGENT_VOICE_PLAY` | `true` | `false` to only save the WAV |
| `AGENT_VOICE_HOST` / `_PORT` | `127.0.0.1` / `7161` | for `agent-voice serve` |

## HTTP server

```sh
agent-voice serve
curl -s localhost:7161/health
curl -s localhost:7161/say -H 'content-type: application/json' \
  -d '{"text": "Deployed.\n<say>It is live. Try not to break it.</say>", "voice": "skippy"}'
# {"spoken": "It is live. Try not to break it.", "wav": "out/skippy-....wav", "voice": "skippy", "source": "tag"}
```

`POST /say` accepts `text`, optional `voice`, optional `mode`; returns 204 when
there was nothing to say. Utterances are serialized, so two agents talking at
once take turns instead of overlapping.

## Python

```python
from agent_voice import Config, Speaker

speaker = Speaker(Config.from_env())
spoken = speaker.speak(agent_reply, "skippy")   # -> Spoken(text, wav, voice, source) or None
```

## Integrations

- `integrations/claude-code/` — two hooks and a toggle that make a Claude Code
  session speak each reply (the origin of this tool). Other hosts need only a
  way to run `agent-voice pipe` with the reply on stdin, or to POST to `/say`.

## Development

```sh
uv venv && uv pip install -e '.[dev]'
pytest && ruff check && ruff format --check && mypy
```

MIT.
