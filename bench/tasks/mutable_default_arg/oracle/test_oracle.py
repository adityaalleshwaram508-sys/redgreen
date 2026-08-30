from collect import accumulate


def test_default_starts_empty_each_call():
    first = accumulate("a")
    second = accumulate("b")
    assert first == ["a"]
    assert second == ["b"]


def test_default_lists_are_independent():
    a = accumulate(1)
    b = accumulate(2)
    assert a is not b
