# Claude Code integration (example)

Two hooks and a toggle turn a Claude Code session into a talking agent. Nothing
here is required by `agent-voice` itself; it is one example of a host feeding
replies into `agent-voice pipe`.

- `speak-mode.sh on [voice] | off | status` -- writes `~/.agent-voice/speak-mode`
  (content = voice name). Wrap it as a slash command if you like
  (`~/.claude/commands/speak-mode.md`).
- `speak_mode_context.py` (UserPromptSubmit) -- while the flag exists, tells the
  model either to end each reply with a `<say>...</say>` line (no writer LLM
  configured) or to reply normally and let the writer choose the line.
- `speak_reply.py` (Stop) -- pulls the reply just finished out of the transcript
  and hands it to `agent-voice pipe` in a detached process, so the hook returns
  immediately. Never replays the same line.

Register them in `~/.claude/settings.json` (paths are absolute; adjust):

```json
{
  "hooks": {
    "UserPromptSubmit": [{"matcher": "*", "hooks": [{"type": "command",
      "command": "python3 /path/to/agent-voice/integrations/claude-code/speak_mode_context.py"}]}],
    "Stop": [{"matcher": "*", "hooks": [{"type": "command",
      "command": "python3 /path/to/agent-voice/integrations/claude-code/speak_reply.py", "timeout": 15}]}]
  }
}
```

Set `AGENT_VOICE_*` in the environment Claude Code runs in (`AGENT_VOICE_TTS_URL`,
`AGENT_VOICE_VOICES_DIR`, optionally `AGENT_VOICE_LLM_URL` / `_MODEL` / `_API_KEY`).
`python3` here must be an interpreter where `agent-voice` is installed.
