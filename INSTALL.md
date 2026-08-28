# Installing agent-voice

Five steps. Steps 1 and 3 are two minutes each; step 2 is the one that takes a
while the first time (downloading the OmniVoice model). After every step,
`agent-voice doctor` tells you what is still missing.

```
1. Install agent-voice            sh install.sh
2. Run an OmniVoice server        (GPU or Apple Silicon box; can be another machine)
3. Make a voice                   voices/<name>/ref.wav + ref.txt
4. (optional) Pick a writer model any OpenAI-compatible endpoint
5. Check and speak                agent-voice doctor && agent-voice speak "hi"
```

---

## 1. Install agent-voice

**Requirements:** Python 3.11 or newer, and something that can play a WAV
(`afplay` on macOS is built in; Linux needs `paplay`, `aplay`, or `ffplay`;
Windows uses the built-in `winsound`).

```sh
git clone https://github.com/rodaddy/agent-voice.git
cd agent-voice
sh install.sh
```

`install.sh` finds a suitable Python, creates `.venv/`, installs the package
into it (using [uv](https://docs.astral.sh/uv/) if you have it, plain `venv` +
`pip` otherwise), writes `agent-voice.env` from the example if you don't have
one, and finishes by running `agent-voice doctor`.

Flags: `--demo` also makes a demo voice from the macOS `say` command
(macOS + ffmpeg); `--dev` also installs pytest/ruff/mypy.

**Without the script:**

```sh
python3 -m venv .venv
.venv/bin/pip install -e .
cp agent-voice.env.example agent-voice.env
```

**Using it from anywhere:** either call `.venv/bin/agent-voice` by full path,
or `pipx install /path/to/agent-voice`, or add `.venv/bin` to your `PATH`.
Config is read from `agent-voice.env` in the *current directory* and from the
environment, so set `AGENT_VOICE_VOICES_DIR` to an absolute path if you run it
from elsewhere.

---

## 2. Run an OmniVoice server

agent-voice does not do the speech synthesis itself. It talks to a small REST
server around [OmniVoice](https://github.com/k2-fsa/OmniVoice), the
open-source zero-shot voice-cloning model (Apache-2.0). Any server exposing
`GET /health` and `POST /synthesize` with the same JSON works; the one people
actually use is scorbo2's `server_omnivoice.py`.

**Where to run it:** a machine with an NVIDIA GPU (8 GB is plenty; a 16 GB
RTX 5060 Ti synthesizes a sentence in about half a second) or an Apple Silicon
Mac (works on MPS in float32; roughly real time on an M-series Air). It can be
a different machine from the one that plays the audio — set
`AGENT_VOICE_TTS_URL` to wherever it is.

```sh
# on the GPU box
git clone https://github.com/k2-fsa/OmniVoice.git
cd OmniVoice
python3 -m venv .venv && . .venv/bin/activate
pip install -e .                         # pulls torch; on Apple Silicon this is the MPS build
pip install fastapi uvicorn loguru soundfile

curl -sLO https://raw.githubusercontent.com/scorbo2/ai-playground/master/TTS/server_omnivoice.py
uvicorn server_omnivoice:app --host 0.0.0.0 --port 8181
```

The first request downloads the model (~3 GB) into your Hugging Face cache
(`HF_HOME` if set). Confirm it is up:

```sh
curl -s http://<server>:8181/health
# {"status":"ok","serverType":"OmniVoice", ...}
```

Then, on the agent-voice machine, put that address in `agent-voice.env`:

```sh
export AGENT_VOICE_TTS_URL=http://<server>:8181
```

**Apple Silicon note:** load the model in `float32`. float16 and bfloat16
crash during weight loading on MPS (measured 2026-08 with torch 2.13).

---

## 3. Make a voice

A voice is a directory under `voices/`:

```
voices/skippy/
  ref.wav        3-10 seconds of the voice, mono, 24 kHz, 16-bit PCM
  ref.txt        the EXACT words spoken in ref.wav, one line
  language.txt   optional, default "English"
  persona.md     optional, see step 4
```

**Try it first with a fake voice (macOS):**

```sh
examples/make-voice-macos.sh voices/demo     # needs ffmpeg: brew install ffmpeg
```

**A real voice, from any recording** (an audiobook, a podcast, a voice memo):

1. Find 3–10 seconds where only that person is speaking, no music, no
   crosstalk. One clean sentence is ideal. A 30-second clip does *not* clone
   better — the model re-reads the clip on every request, so long clips are
   just slower.
2. Cut and convert it with ffmpeg (`-ss` start, `-t` length in seconds):

   ```sh
   mkdir -p voices/skippy
   ffmpeg -ss 8:43:09 -i book.m4b -t 7.5 -vn -ac 1 -ar 24000 -sample_fmt s16 voices/skippy/ref.wav
   ```

3. Write the exact transcript to `voices/skippy/ref.txt`. Punctuation and
   casing matter less than getting every word right; a wrong word here makes
   the clone drift. (If you have whisper handy, draft with it and fix by hand.)
4. Cut three or four candidates and pick by ear — clips from the same speaker
   clone noticeably differently. `agent-voice speak --voice skippy-b "..."`
   for each, keep the winner as `voices/skippy`.

`agent-voice voices` lists what it found; `agent-voice doctor` warns about
clips that are too long or not PCM WAV.

---

## 4. (Optional) Pick a writer model

Without a writer, agent-voice speaks the `<say>...</say>` line an agent wrote,
or the whole text. With a writer, you can pipe in any reply and a small model
decides what the *character* would say about it. This is where the persona
comes alive.

Any OpenAI-compatible chat endpoint works. Local options that are known to
work:

| Server | `AGENT_VOICE_LLM_URL` | `AGENT_VOICE_LLM_MODEL` |
|---|---|---|
| [Ollama](https://ollama.com) | `http://127.0.0.1:11434` | e.g. `qwen3:8b` |
| [LM Studio](https://lmstudio.ai) | `http://127.0.0.1:1234` | the loaded model's id |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) `llama-server` | `http://127.0.0.1:8080` | whatever it reports in `/v1/models` |
| [oMLX](https://github.com/jundot/omlx) (Apple Silicon) | `http://127.0.0.1:11434` | e.g. `Qwen3.5-9B-4bit` |
| OpenAI / any hosted API | its base URL | model name; set `AGENT_VOICE_LLM_API_KEY` |

An 8–9B model is plenty; it writes the line in 2–3 seconds on a laptop.
Thinking models are asked not to think (`enable_thinking: false`) and their
`<think>` blocks are stripped if they think anyway.

```sh
export AGENT_VOICE_LLM_URL=http://127.0.0.1:11434
export AGENT_VOICE_LLM_MODEL=qwen3:8b
```

Give the voice a personality in `voices/<name>/persona.md` — a few lines of
*who this is*, written as a system prompt. `examples/persona-ship-ai.md` is a
starting point. The writer is told separately to keep it to one or two spoken
sentences, so the persona file only needs to describe character.

---

## 5. Check and speak

```sh
.venv/bin/agent-voice doctor
```

```
[ok  ] python         3.12.4
[ok  ] player         afplay
[ok  ] tts            http://gpu-box:8181 (OmniVoice)
[ok  ] voices         demo, skippy
[ok  ] writer         qwen3:8b @ http://127.0.0.1:11434
[ok  ] ffmpeg         found (for making voices)
```

Every `FAIL` line comes with a `fix:` line. When it is green:

```sh
.venv/bin/agent-voice speak --voice skippy "Say something, dum-dum."
printf 'All 41 tests pass after the refactor.\n' | .venv/bin/agent-voice pipe --voice skippy
.venv/bin/agent-voice serve      # then POST /say from anything
```

---

## Hooking up an agent

- **It prints to stdout:** `my-agent | agent-voice pipe --voice skippy`.
- **It can make HTTP calls:** run `agent-voice serve` and POST
  `{"text": reply, "voice": "skippy"}` to `http://127.0.0.1:7161/say`.
- **It is Python:** `from agent_voice import Config, Speaker` — see the README.
- **It is Claude Code:** `integrations/claude-code/README.md`.

For the cleanest results, tell the agent about the tag: *"End every reply
with one spoken line wrapped as `<say>...</say>`: one or two short sentences,
in character, plain words only."* Then the agent itself decides what is worth
saying, and the writer model is only a fallback.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `tts ... not answering GET /health` | Server not running, wrong port, or firewall. `curl http://<server>:8181/health` from the agent-voice machine. |
| `502` from `/say`, or `HTTPStatusError 422` | The TTS server rejected the request — usually `num_steps` outside 10–20 on scorbo2's server, or a `ref.wav` that isn't PCM. |
| Speech is slow (10+ s per sentence) | TTS running on CPU, or a long `ref.wav`. Cut the clip to under 10 s; use a GPU / MPS box. |
| Voice sounds nothing like the clip | `ref.txt` doesn't match the audio, or the clip has music/crosstalk. Re-cut and re-transcribe. |
| Nothing plays but a WAV is written | No player found — `doctor` says which to install — or `AGENT_VOICE_PLAY=false`. |
| Writer lines are flat or cut off | Try a larger model, lower `AGENT_VOICE_MAX_WORDS`, or improve `persona.md`. Lines are never cut mid-sentence; a cut-off means the model wrote past the cap. |
| Two agents talk over each other | They can't through one `agent-voice serve` — it serializes. Two separate processes can; point both at one server. |
| `agent-voice: command not found` | It's in `.venv/bin/`. Use the full path, add it to `PATH`, or `pipx install .`. |
