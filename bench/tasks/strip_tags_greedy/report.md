# strip_tags eats the text between tags

`strip_tags(html)` should remove tags but keep the text. With more than one tag it removes
everything between the first `<` and the last `>`:

    >>> from html_tools import strip_tags
    >>> strip_tags("<b>hi</b>")
    ''              # expected 'hi'
    >>> strip_tags("x<br>y<br>z")
    'xz'            # expected 'xyz'

## Expected
Only the tags are removed; the visible text survives.
