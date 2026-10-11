# prettyisbns

[![PyPI - Version](https://img.shields.io/pypi/v/prettyisbns)](https://pypi.org/project/prettyisbns/)
[![Tests](https://github.com/xymaxim/prettyisbns/actions/workflows/ci.yml/badge.svg)](https://github.com/xymaxim/prettyisbns/actions/workflows/ci.yml)

A Python package for normalizing, fixing, and formatting ISBNs to make them pretty.

[Source](https://github.com/xymaxim/prettyisbns)
[Documentation](https://prettyisbns.readthedocs.io/en/latest/)
[Changelog](https://prettyisbns.readthedocs.io/en/latest/changelog.html)

## Installation

The package is available on PyPI:

```bash
pip install prettyisbns
```

## Usage

### Normalize and fix ISBNs

Normalize an ISBN and fix its check digit:

```pycon
>>> from prettyisbns import normalize
>>> canonical = normalize("23-6590-117-X", fix=True)
>>> canonical
CanonicalISBN(9782365901178)
```

The result is a canonical, normalized ISBN-13 string without hyphens.

### Format ISBNs

Format a canonical ISBN with hyphens to split it into elements:

```pycon
>>> canonical.hyphenate()
'978-2-36590-117-8'
```

To normalize, fix, and format in one step, use the
[`pretty()`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.html#prettyisbns.pretty)
shortcut:

```pycon
>>> from prettyisbns import pretty
>>> pretty("23-6590-117-X")
'978-2-36590-117-8'
```

Formatting relies on the registration groups and registrant ranges from the
[International ISBN Agency](https://www.isbn-international.org/), which are
stored in the auto-generated
[prettyisbns.ranges](https://github.com/xymaxim/prettyisbns/blob/main/src/prettyisbns/ranges.py)
module. Ranges can be redefined, which may cause a discrepancy with the
module. In that case, update the package or open an issue.

### Access ISBN elements

Internally, formatting is done by
[`ISBNLayout`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.isbn.html#prettyisbns.isbn.ISBNLayout),
which splits an ISBN into bookland, registration group, registrant, publication,
and check digit elements. You can access it through the
[`layout`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.isbn.html#prettyisbns.isbn.CanonicalISBN.layout)
property, which supports slicing for a granular output:

```pycon
# Split the canonical ISBN into its elements
>>> canonical.layout
ISBNLayout(
    bookland='978',
    group='2',
    registrant='36590',
    publication='117',
    check_digit='8',
)

# Get the group prefix
>>> canonical.layout[:2]
'978-2'

# Get the registrant prefix
>>> canonical.layout[:3]
'978-2-36590'
```

### Validate ISBNs

Check an ISBN's check digit, registration group, and registrant range with
[`validate()`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.isbn.html#prettyisbns.isbn.CanonicalISBN.validate).
It returns a
[`ValidationResult`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.isbn.html#prettyisbns.isbn.ValidationResult),
which is truthy only when the ISBN is valid:

```python
if result := canonical.validate():
    print("valid")
else:
    print(f"invalid: {result.errors}")
```

### Handle errors

Normalizing raises
[`NotISBNError`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.errors.html#prettyisbns.errors.NotISBNError)
if a value is neither ISBN-10 nor ISBN-13, and formatting raises
[`InvalidISBNError`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.errors.html#prettyisbns.errors.InvalidISBNError)
if the registration group or registrant range of an ISBN is not defined. Its
[`reason`](https://prettyisbns.readthedocs.io/en/latest/api/prettyisbns.errors.html#prettyisbns.errors.InvalidISBNError)
attribute tells what exactly is wrong:

```python
from prettyisbns import pretty
from prettyisbns.errors import InvalidISBNError, NotISBNError

try:
    prettied = pretty(value)
except NotISBNError:
    # The value is neither ISBN-10 nor ISBN-13
    ...
except InvalidISBNError as error:
    # The ISBN cannot be formatted, see error.reason
    ...
```

## API

See the full [API](https://prettyisbns.readthedocs.io/en/latest/api/index.html)
reference in the documentation.


## License

MIT.
