"""Pagination helpers."""


def num_pages(total_items, page_size):
    """Number of pages needed to show ``total_items`` at ``page_size`` per page."""
    return -(-total_items // page_size)
