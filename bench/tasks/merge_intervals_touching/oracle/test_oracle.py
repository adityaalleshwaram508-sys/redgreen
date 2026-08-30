import random

from ranges import merge_intervals


def _reference(intervals):
    if not intervals:
        return []
    ordered = sorted([a, b] for a, b in intervals)
    out = [ordered[0][:]]
    for a, b in ordered[1:]:
        if a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def test_touching_pair():
    assert merge_intervals([[1, 3], [3, 5]]) == [[1, 5]]


def test_touching_chain():
    assert merge_intervals([[1, 2], [2, 3], [3, 4]]) == [[1, 4]]


def test_touching_unsorted():
    assert merge_intervals([[3, 5], [1, 3]]) == [[1, 5]]


def test_touching_with_gap():
    assert merge_intervals([[1, 3], [3, 5], [7, 9]]) == [[1, 5], [7, 9]]


def test_zero_width_boundary():
    assert merge_intervals([[1, 4], [4, 4], [4, 8], [10, 10]]) == [[1, 8], [10, 10]]


def test_property_matches_reference():
    rnd = random.Random(1234)
    for _ in range(200):
        ivs = []
        for _ in range(rnd.randint(0, 6)):
            a = rnd.randint(0, 10)
            ivs.append([a, a + rnd.randint(0, 5)])
        assert merge_intervals(ivs) == _reference(ivs)
