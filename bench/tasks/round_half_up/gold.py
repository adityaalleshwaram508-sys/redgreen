"""Rounding helpers."""
import math


def round_half_up(x):
    """Round to the nearest integer, with halves rounding up."""
    return math.floor(x + 0.5)
