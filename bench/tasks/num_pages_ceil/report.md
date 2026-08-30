# num_pages drops the final partial page

`num_pages(total_items, page_size)` returns the number of pages needed. A partial last
page is not counted:

    >>> from pagination import num_pages
    >>> num_pages(21, 10)
    2               # expected 3 (last page holds the 21st item)

## Expected
Any leftover items need their own page. `num_pages(21, 10) == 3`, `num_pages(9, 10) == 1`,
`num_pages(0, 10) == 0`.
