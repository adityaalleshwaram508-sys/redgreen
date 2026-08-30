from text import slugify


def test_collapses_whitespace():
    assert slugify("Hello   World") == "hello-world"


def test_strips_edges():
    assert slugify("  Hello  ") == "hello"


def test_drops_punctuation():
    assert slugify("Hello, World!") == "hello-world"
