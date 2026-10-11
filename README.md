# prettyisbns

[![Tests](https://github.com/xymaxim/prettyisbns/actions/workflows/ci.yml/badge.svg)](https://github.com/xymaxim/prettyisbns/actions/workflows/ci.yml)

A Python package for normalizing, fixing, and formatting ISBNs to make them pretty.

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

The result is a `CanonicalISBN`, a normalized ISBN-13 string without hyphens.

### Format ISBNs

Format a canonical ISBN with hyphens:

```pycon
>>> canonical.hyphenate()
'978-2-36590-117-8'
```

To normalize, fix, and format in one step, use the `pretty()` shortcut:

```pycon
>>> from prettyisbns import pretty
>>> pretty("23-6590-117-X")
'978-2-36590-117-8'
```

Formatting relies on the registration groups and registrant ranges from the
[International ISBN Agency](https://www.isbn-international.org/), which are
stored in the auto-generated `prettyisbns.ranges` module. Ranges can be redefined,
which may cause a discrepancy with the module. In that case, update the package
or open an issue.

### Access ISBN elements

Internally, formatting is done by `ISBNLayout`, which splits an ISBN into
bookland, registration group, registrant, publication, and check digit
elements. You can access it through the `layout` property, which supports
slicing for a granular output:

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
`validate()`. It returns a `ValidationResult`, which is truthy only when the
ISBN is valid:

```python
if result := canonical.validate():
    print("valid")
else:
    print(f"invalid: {result.errors}")
```

### Handle errors

Normalizing raises `NotISBNError` if a value is neither ISBN-10 nor ISBN-13,
and formatting raises `InvalidISBNError` if the registration group or
registrant range of an ISBN is not defined. Its `reason` attribute tells what
exactly is wrong:

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
