from agent_voice.writer import Writer, clean, trim_to_sentences
from tests.conftest import fake_llm


def test_trim_keeps_whole_sentences() -> None:
    text = "One two three. Four five six seven. Eight nine ten eleven twelve."
    assert trim_to_sentences(text, 6) == "One two three."
    assert trim_to_sentences(text, 100) == text


def test_trim_without_sentence_end_appends_period() -> None:
    assert trim_to_sentences("a b c d e f", 3) == "a b c."


def test_clean_strips_thinking_and_emphasis() -> None:
    assert clean("<think>hmm\nyes</think> **Fine**, done.") == "Fine, done."


def test_writer_sends_persona_and_reply() -> None:
    calls: list[dict] = []
    w = Writer(
        "http://llm.test/",
        "m",
        api_key="k",
        max_words=10,
        transport=fake_llm("Ok. Go.", calls),
    )
    assert w.line_for("long reply", "PERSONA") == "Ok. Go."
    body = calls[0]
    assert body["model"] == "m"
    assert body["messages"][0]["content"].startswith("PERSONA")
    assert "10 words" in body["messages"][0]["content"]
    assert body["messages"][1]["content"] == "long reply"
