#!/bin/sh
# Any agent's reply on stdin becomes speech. With AGENT_VOICE_LLM_URL set, the
# writer picks the line; without it, a <say> tag is spoken, else the text itself.
printf 'Refactored the parser and all 41 tests pass.\n\n<say>Parser is fixed, tests are green, you can stop hovering.</say>\n' \
  | agent-voice pipe --voice "${1:-demo}"
