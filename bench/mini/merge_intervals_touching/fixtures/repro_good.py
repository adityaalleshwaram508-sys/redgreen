from ranges import merge_intervals


def test_touching_intervals_merge():
    assert merge_intervals([[1, 3], [3, 5]]) == [[1, 5]]
