# index_of misses elements at the ends of the list

`index_of(sorted_list, target)` returns the index of `target`, or -1. It finds values in
the middle but returns -1 for the first and last elements:

    >>> from search import index_of
    >>> index_of([10, 20, 30], 10)
    -1              # expected 0
    >>> index_of([10, 20, 30], 30)
    -1              # expected 2

## Expected
Every present value is found at its correct index; only genuinely absent values return -1.
