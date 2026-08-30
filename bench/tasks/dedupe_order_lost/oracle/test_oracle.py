from sequences import dedupe


def test_preserves_first_occurrence_order():
    assert dedupe([3, 1, 2, 1, 3]) == [3, 1, 2]


def test_strings_keep_order():
    assert dedupe(["b", "a", "b", "c"]) == ["b", "a", "c"]


def test_already_unique_is_unchanged():
    assert dedupe([5, 4, 3]) == [5, 4, 3]
