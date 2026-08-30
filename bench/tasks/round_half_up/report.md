# round_half_up rounds .5 the wrong way

`round_half_up(x)` should round to the nearest integer with halves going up. It uses
Python's built-in `round`, which rounds halves to the nearest even number:

    >>> from rounding import round_half_up
    >>> round_half_up(0.5)
    0               # expected 1
    >>> round_half_up(2.5)
    2               # expected 3

## Expected
Exact halves always round up: 0.5 -> 1, 1.5 -> 2, 2.5 -> 3.
