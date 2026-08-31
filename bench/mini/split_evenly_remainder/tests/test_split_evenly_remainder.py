from money import split_evenly


def test_even_split():
    assert split_evenly(100, 4) == [25, 25, 25, 25]


def test_single_person_gets_everything():
    assert split_evenly(100, 1) == [100]


def test_zero_total():
    assert split_evenly(0, 3) == [0, 0, 0]
