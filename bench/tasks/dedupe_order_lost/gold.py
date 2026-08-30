"""Sequence helpers."""


def dedupe(items):
    """Remove duplicates, preserving the order of first occurrence."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
