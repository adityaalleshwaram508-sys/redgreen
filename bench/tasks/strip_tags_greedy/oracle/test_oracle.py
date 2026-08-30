from html_tools import strip_tags


def test_keeps_text_inside_a_pair():
    assert strip_tags("<b>hi</b>") == "hi"


def test_multiple_tag_pairs():
    assert strip_tags("<i>a</i> and <i>b</i>") == "a and b"


def test_text_between_two_tags():
    assert strip_tags("x<br>y<br>z") == "xyz"
