"""Small collection helpers."""


def accumulate(value, into=None):
    """Append ``value`` to ``into`` (a fresh list by default) and return it."""
    if into is None:
        into = []
    into.append(value)
    return into
