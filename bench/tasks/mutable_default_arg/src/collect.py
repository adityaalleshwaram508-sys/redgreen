"""Small collection helpers."""


def accumulate(value, into=[]):
    """Append ``value`` to ``into`` (a fresh list by default) and return it."""
    into.append(value)
    return into
