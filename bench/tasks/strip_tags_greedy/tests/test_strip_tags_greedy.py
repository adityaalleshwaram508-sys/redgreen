from html_tools import strip_tags


def test_no_tags():
    assert strip_tags("plain text") == "plain text"


def test_self_closing_tag():
    assert strip_tags("<br>") == ""


def test_trailing_text_after_open_tag():
    assert strip_tags("<p>hello") == "hello"
