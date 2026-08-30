"""Tiny HTML helpers."""
import re


def strip_tags(html):
    """Remove HTML tags, keeping the text between them."""
    return re.sub(r"<.*?>", "", html)
