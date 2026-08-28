from agent_voice.tags import spoken_line, strip_markup


def test_plain_tag() -> None:
    assert spoken_line("Done.\n\n<say>Hi there.</say>") == "Hi there."


def test_quoted_tags_in_code_are_ignored() -> None:
    reply = (
        "The `<say>` line is spoken; write `<say>...</say>` last.\n"
        "```\n<say>not this</say>\n```\n<say>Only this.</say>"
    )
    assert spoken_line(reply) == "Only this."


def test_last_tag_wins_and_whitespace_collapses() -> None:
    assert (
        spoken_line("<say>first</say> x <say>the\n  last one</say>") == "the last one"
    )


def test_no_tag() -> None:
    assert spoken_line("text mentioning <say> once") is None


def test_strip_markup() -> None:
    assert strip_markup("**Bold** `code` and\n\n# heading") == "Bold and heading"
