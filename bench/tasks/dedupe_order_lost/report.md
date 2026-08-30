# dedupe scrambles the order of the items

`dedupe(items)` should remove duplicates while keeping the order in which items first
appear. It returns them in an unrelated order:

    >>> from sequences import dedupe
    >>> dedupe([3, 1, 2, 1, 3])
    [1, 2, 3]       # expected [3, 1, 2]

## Expected
Duplicates are dropped, and the surviving items keep their first-seen order.
