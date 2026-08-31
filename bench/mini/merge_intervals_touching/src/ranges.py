"""Interval utilities used across scheduling and range-collapsing code paths."""
from __future__ import annotations


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Collapse ``[start, end]`` intervals into the minimal set of non-overlapping
    intervals, sorted by start. Intervals are treated as inclusive ranges.
    """
    if not intervals:
        return []
    ordered = sorted((list(iv) for iv in intervals), key=lambda iv: (iv[0], iv[1]))
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start < last[1]:          # only merges on strict overlap; touching ranges slip through
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged
