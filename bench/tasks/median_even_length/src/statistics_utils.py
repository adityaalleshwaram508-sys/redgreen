"""Small statistics helpers."""


def median(values):
    """Return the median of a non-empty list of numbers."""
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2]
