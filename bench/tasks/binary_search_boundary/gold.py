"""Binary search over a sorted list."""


def index_of(sorted_list, target):
    """Return the index of ``target`` in ``sorted_list``, or -1 if absent."""
    lo, hi = 0, len(sorted_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_list[mid] == target:
            return mid
        if sorted_list[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return -1
