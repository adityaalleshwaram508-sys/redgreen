# accumulate() remembers values from previous calls

`accumulate(value)` is meant to return a fresh list containing just `value` when no
target list is given. Instead, values leak between calls:

    >>> from collect import accumulate
    >>> accumulate("a")
    ['a']
    >>> accumulate("b")
    ['a', 'b']      # expected ['b']

## Expected
Each call with no target list should start from an empty list. Two such calls should not
share state.
