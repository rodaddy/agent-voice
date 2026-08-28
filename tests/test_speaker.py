from pathlib import Path

import pytest

from agent_voice.config import Config
from agent_voice.speaker import Speaker
from agent_voice.voices import VoiceNotFoundError, list_voices, load_voice
from tests.conftest import fake_llm, fake_tts


def test_library(library: Path) -> None:
    assert list_voices(library) == ["alpha"]
    v = load_voice(library, "")
    assert v.name == "alpha" and v.ref_text == "Hello there." and "Alpha" in v.persona
    with pytest.raises(VoiceNotFoundError):
        load_voice(library, "nope")


def test_tag_beats_writer(config: Config) -> None:
    tts: list[dict] = []
    llm: list[dict] = []
    s = Speaker(
        config, tts_transport=fake_tts(tts), llm_transport=fake_llm("unused", llm)
    )
    spoken = s.speak("Report.\n<say>Tagged line.</say>")
    assert (
        spoken is not None and spoken.source == "tag" and spoken.text == "Tagged line."
    )
    assert tts[0]["text"] == "Tagged line." and tts[0]["prompt_text"] == "Hello there."
    assert tts[0]["num_steps"] == 10 and llm == []
    assert spoken.wav.is_file() and spoken.wav.parent == config.out_dir


def test_writer_when_no_tag(config: Config) -> None:
    tts: list[dict] = []
    llm: list[dict] = []
    s = Speaker(
        config,
        tts_transport=fake_tts(tts),
        llm_transport=fake_llm("Writer said this.", llm),
    )
    spoken = s.speak("A long technical reply with `code`.")
    assert (
        spoken is not None
        and spoken.source == "writer"
        and spoken.text == "Writer said this."
    )
    assert "Alpha" in llm[0]["messages"][0]["content"]


def test_direct_when_no_writer(config: Config) -> None:
    tts: list[dict] = []
    s = Speaker(
        Config(**{**config.__dict__, "llm_url": ""}), tts_transport=fake_tts(tts)
    )
    spoken = s.speak("**Plain** text `x`.")
    assert (
        spoken is not None
        and spoken.source == "direct"
        and spoken.text == "Plain text ."
    )


def test_tag_mode_is_silent_without_tag(config: Config) -> None:
    s = Speaker(config, tts_transport=fake_tts([]), llm_transport=fake_llm("x", []))
    assert s.speak("no tag here", mode="tag") is None


def test_config_from_env(tmp_path: Path) -> None:
    c = Config.from_env(
        {
            "AGENT_VOICE_PORT": "7171",
            "AGENT_VOICE_PLAY": "false",
            "AGENT_VOICE_VOICES_DIR": str(tmp_path),
            "AGENT_VOICE_GUIDANCE_SCALE": "1.5",
        }
    )
    assert (
        c.port == 7171
        and c.play is False
        and c.voices_dir == tmp_path
        and c.guidance_scale == 1.5
    )
    assert not c.has_writer
