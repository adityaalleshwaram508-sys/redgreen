"""Text helpers."""
import re


def slugify(text):
    """Turn ``text`` into a URL slug."""
    return re.sub(r"\s", "-", text.lower())
