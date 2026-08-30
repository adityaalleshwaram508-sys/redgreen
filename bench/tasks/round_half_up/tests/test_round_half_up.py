from rounding import round_half_up


def test_rounds_down_below_half():
    assert round_half_up(2.3) == 2


def test_rounds_up_above_half():
    assert round_half_up(2.7) == 3


def test_integer_value():
    assert round_half_up(5.0) == 5
