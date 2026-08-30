from ranges import merge_intervals


def test_disjoint():
    assert merge_intervals([[1, 2], [5, 6]]) == [[1, 2], [5, 6]]


def test_overlap():
    assert merge_intervals([[1, 4], [2, 5]]) == [[1, 5]]


def test_nested():
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]


def test_unsorted_input():
    assert merge_intervals([[5, 6], [1, 4], [2, 3]]) == [[1, 4], [5, 6]]


def test_empty():
    assert merge_intervals([]) == []


def test_single():
    assert merge_intervals([[3, 7]]) == [[3, 7]]
