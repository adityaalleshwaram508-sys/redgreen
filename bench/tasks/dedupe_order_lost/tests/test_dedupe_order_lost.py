from sequences import dedupe


def test_removes_duplicates():
    assert set(dedupe([1, 1, 2, 3, 3])) == {1, 2, 3}


def test_length_after_dedupe():
    assert len(dedupe([1, 1, 1])) == 1


def test_empty():
    assert dedupe([]) == []
