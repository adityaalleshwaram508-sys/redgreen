"""Money splitting helpers. All amounts are integer cents."""


def split_evenly(total_cents, people):
    """Split ``total_cents`` across ``people`` as evenly as possible.

    The returned shares must sum to ``total_cents``.
    """
    share, remainder = divmod(total_cents, people)
    return [share + (1 if i < remainder else 0) for i in range(people)]
