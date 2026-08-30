from search import index_of


def test_find_middle():
    assert index_of([1, 2, 3, 4, 5], 3) == 2


def test_absent_returns_minus_one():
    assert index_of([1, 2, 3, 4, 5], 9) == -1


def test_empty_list():
    assert index_of([], 5) == -1
