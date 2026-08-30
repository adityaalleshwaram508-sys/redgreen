"""Text helpers."""
import re


def slugify(text):
    """Turn ``text`` into a URL slug."""
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return text.strip("-")
