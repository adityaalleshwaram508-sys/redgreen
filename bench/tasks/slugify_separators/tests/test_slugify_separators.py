from text import slugify


def test_basic():
    assert slugify("Hello World") == "hello-world"


def test_lowercases():
    assert slugify("PYTHON") == "python"


def test_single_word():
    assert slugify("Test") == "test"
