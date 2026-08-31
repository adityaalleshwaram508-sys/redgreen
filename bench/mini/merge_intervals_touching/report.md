# merge_intervals leaves touching ranges unmerged

When two ranges share an endpoint — e.g. `[1, 3]` and `[3, 5]` — `merge_intervals`
returns them as two separate ranges `[[1, 3], [3, 5]]` instead of merging them into
`[[1, 5]]`.

Overlapping ranges (`[1, 4]` and `[2, 5]`) merge correctly, so this only shows up when
ranges *touch* at the boundary rather than overlap.

## Repro

    >>> from ranges import merge_intervals
    >>> merge_intervals([[1, 3], [3, 5]])
    [[1, 3], [3, 5]]      # expected [[1, 5]]

## Expected

A range that starts exactly where the previous one ends is contiguous and should be
combined. Intervals are inclusive.
