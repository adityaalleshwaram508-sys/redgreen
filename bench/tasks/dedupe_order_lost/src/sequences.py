"""Sequence helpers."""


def dedupe(items):
    """Remove duplicates, preserving the order of first occurrence."""
    return list(set(items))
