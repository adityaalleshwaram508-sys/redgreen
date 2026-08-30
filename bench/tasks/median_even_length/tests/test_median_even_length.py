from statistics_utils import median


def test_odd_length():
    assert median([3, 1, 2]) == 2


def test_single_value():
    assert median([5]) == 5


def test_odd_length_sorted():
    assert median([1, 2, 3, 4, 5]) == 3
