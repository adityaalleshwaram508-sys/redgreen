from collect import accumulate


def test_appends_to_given_list():
    assert accumulate(1, []) == [1]


def test_appends_multiple_to_a_given_list():
    bucket = []
    accumulate(1, bucket)
    accumulate(2, bucket)
    assert bucket == [1, 2]


def test_returns_the_same_list_object():
    bucket = []
    assert accumulate(9, bucket) is bucket
