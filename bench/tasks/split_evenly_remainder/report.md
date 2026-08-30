# split_evenly loses cents when the total doesn't divide evenly

`split_evenly(total_cents, people)` should hand out every cent — the shares must sum back
to the total. When the total isn't divisible, cents go missing:

    >>> from money import split_evenly
    >>> split_evenly(100, 3)
    [33, 33, 33]        # sums to 99, expected to sum to 100

## Expected
The shares sum to `total_cents`, differ from each other by at most one cent, and there are
exactly `people` of them.
