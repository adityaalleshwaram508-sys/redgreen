from money import split_evenly


def test_shares_always_sum_to_total():
    for total in range(0, 51):
        for people in range(1, 8):
            shares = split_evenly(total, people)
            assert len(shares) == people
            assert sum(shares) == total
            assert max(shares) - min(shares) <= 1


def test_remainder_is_spread():
    assert split_evenly(100, 3) == [34, 33, 33]
