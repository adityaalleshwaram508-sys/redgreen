from pagination import num_pages


def test_exact_multiple():
    assert num_pages(20, 10) == 2


def test_zero_items():
    assert num_pages(0, 10) == 0


def test_one_full_page():
    assert num_pages(10, 10) == 1
