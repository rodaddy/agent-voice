#!/bin/sh
# speak-mode.sh on [voice] | off | status
flag="$HOME/.agent-voice/speak-mode"
mkdir -p "$HOME/.agent-voice"
case "${1:-status}" in
  on)   printf '%s\n' "${2:-}" > "$flag"; echo "speak mode ON (voice: ${2:-default})" ;;
  off)  [ -f "$flag" ] && mv "$flag" "$flag.off"; echo "speak mode OFF" ;;
  status) if [ -f "$flag" ]; then echo "speak mode ON (voice: $(cat "$flag"))"; else echo "speak mode OFF"; fi ;;
  *) echo "usage: speak-mode.sh on [voice] | off | status" >&2; exit 2 ;;
esac
