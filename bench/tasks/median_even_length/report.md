# median is wrong for even-length inputs

`median(values)` returns the middle value. For an even number of values it should average
the two middle ones, but it returns just one of them:

    >>> from statistics_utils import median
    >>> median([1, 2, 3, 4])
    3               # expected 2.5

## Expected
Odd length: the middle value. Even length: the mean of the two middle values.
