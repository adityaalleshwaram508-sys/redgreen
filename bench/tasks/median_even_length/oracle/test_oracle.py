from statistics_utils import median


def test_even_length_averages_two_middles():
    assert median([1, 2, 3, 4]) == 2.5


def test_even_two_values():
    assert median([10, 20]) == 15


def test_even_unsorted():
    assert median([4, 1, 3, 2]) == 2.5
