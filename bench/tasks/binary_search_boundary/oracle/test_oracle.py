from search import index_of


def test_finds_every_index():
    values = [10, 20, 30, 40, 50]
    for i, x in enumerate(values):
        assert index_of(values, x) == i


def test_first_and_last():
    assert index_of([1, 2, 3], 1) == 0
    assert index_of([1, 2, 3], 3) == 2


def test_single_element():
    assert index_of([7], 7) == 0
