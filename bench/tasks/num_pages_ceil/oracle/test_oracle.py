import math

from pagination import num_pages


def test_partial_last_page():
    assert num_pages(21, 10) == 3
    assert num_pages(1, 10) == 1
    assert num_pages(9, 10) == 1


def test_matches_ceiling_division():
    for total in range(0, 40):
        for size in range(1, 8):
            assert num_pages(total, size) == math.ceil(total / size)
