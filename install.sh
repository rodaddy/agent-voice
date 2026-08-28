#!/bin/sh
# agent-voice installer -- one command, then `agent-voice doctor` says what is left.
#
#   sh install.sh            venv + install + agent-voice.env + doctor
#   sh install.sh --demo     also make a demo voice from the macOS `say` command
#   sh install.sh --dev      also install pytest / ruff / mypy
#
# Plain POSIX sh. Safe to re-run: it reuses .venv and never overwrites agent-voice.env.
set -eu

cd "$(dirname "$0")"
DEV=0
DEMO=0
for arg in "$@"; do
  case "$arg" in
    --dev) DEV=1 ;;
    --demo) DEMO=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "install.sh: unknown option '$arg' (try --help)" >&2; exit 2 ;;
  esac
done

say() { printf '\n==> %s\n' "$*"; }

# 1. Python 3.11+ ------------------------------------------------------------
find_python() {
  for candidate in python3.13 python3.12 python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

say "Looking for Python 3.11+"
if ! PY=$(find_python); then
  cat >&2 <<'EOF'
No Python 3.11+ found on PATH.
  macOS:   brew install python@3.12      (or https://www.python.org/downloads/)
  Debian:  sudo apt install python3.12 python3.12-venv
  Fedora:  sudo dnf install python3.12
  Windows: https://www.python.org/downloads/  (then run this in Git Bash or WSL)
  any:     curl -LsSf https://astral.sh/uv/install.sh | sh && uv python install 3.12
EOF
  exit 1
fi
echo "using $PY ($("$PY" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))'))"

# 2. Virtualenv + package ----------------------------------------------------
EXTRAS=""
[ "$DEV" -eq 1 ] && EXTRAS="[dev]"

say "Installing into .venv"
if command -v uv >/dev/null 2>&1; then
  [ -d .venv ] || uv venv -q .venv --python "$PY"
  uv pip install -q --python .venv/bin/python -e ".${EXTRAS}"
else
  [ -d .venv ] || "$PY" -m venv .venv
  .venv/bin/python -m pip install -q --upgrade pip
  .venv/bin/python -m pip install -q -e ".${EXTRAS}"
fi
echo "installed: $(.venv/bin/agent-voice --help 2>/dev/null | head -1 || echo 'agent-voice')"

# 3. Config file --------------------------------------------------------------
if [ ! -f agent-voice.env ]; then
  cp agent-voice.env.example agent-voice.env
  echo "wrote agent-voice.env (edit AGENT_VOICE_TTS_URL to point at your OmniVoice server)"
else
  echo "keeping your existing agent-voice.env"
fi

# 4. Optional demo voice ------------------------------------------------------
if [ "$DEMO" -eq 1 ]; then
  say "Making a demo voice"
  if [ "$(uname -s)" != "Darwin" ]; then
    echo "--demo uses the macOS 'say' command; on this OS make a voice by hand (INSTALL.md step 3)" >&2
  elif ! command -v ffmpeg >/dev/null 2>&1; then
    echo "--demo needs ffmpeg: brew install ffmpeg" >&2
  else
    sh examples/make-voice-macos.sh voices/demo
  fi
fi

# 5. Report -----------------------------------------------------------------
say "Checking the setup (agent-voice doctor)"
.venv/bin/agent-voice doctor || true

cat <<'EOF'

Next:
  1. edit agent-voice.env            -> AGENT_VOICE_TTS_URL = your OmniVoice server (INSTALL.md step 2)
  2. add a voice under voices/       -> ref.wav + ref.txt                        (INSTALL.md step 3)
  3. .venv/bin/agent-voice doctor    -> until it is all green
  4. .venv/bin/agent-voice speak --voice <name> "It works."
EOF
