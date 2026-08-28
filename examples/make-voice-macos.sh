#!/bin/sh
# Make a test voice from the macOS `say` command so you can try agent-voice
# before you have a real reference clip:  examples/make-voice-macos.sh voices/demo
set -eu
dir="${1:-voices/demo}"
text="This is a short reference clip, recorded so the model can learn how this voice sounds."
mkdir -p "$dir"
say -v Samantha -o "$dir/ref.aiff" "$text"
ffmpeg -y -loglevel error -i "$dir/ref.aiff" -ac 1 -ar 24000 -sample_fmt s16 "$dir/ref.wav"
printf '%s\n' "$text" > "$dir/ref.txt"
printf 'English\n' > "$dir/language.txt"
echo "voice written to $dir (add a persona.md to give it a personality)"
