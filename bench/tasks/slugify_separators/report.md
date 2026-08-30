# slugify leaves doubled and trailing hyphens

`slugify(text)` should produce a clean URL slug. Runs of whitespace become runs of
hyphens, punctuation is left in, and edges aren't trimmed:

    >>> from text import slugify
    >>> slugify("Hello   World")
    'hello---world'     # expected 'hello-world'
    >>> slugify("  Hello, World!  ")
    '--hello,-world!--' # expected 'hello-world'

## Expected
Lowercase, non-alphanumeric runs collapse to a single hyphen, and leading/trailing hyphens
are removed.
