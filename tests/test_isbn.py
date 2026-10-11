from itertools import islice

import pytest

from prettyisbns.errors import InvalidISBNReason
from prettyisbns.isbn import (
    CanonicalISBN,
    ISBNLayout,
    ValidationResult,
    generate_isbns,
    is_isbn,
    normalize,
    pretty,
)


@pytest.mark.parametrize(
    "isbn, expected",
    [
        ("9780000000002", "9780000000002"),
        ("9780000000003", "9780000000003"),
        ("0000000002", "9780000000002"),
        ("978000000000X", "978000000000X"),
        ("978000000000x", "978000000000X"),
        # ISBN-10 inputs are converted, recomputing the check digit
        ("0-306-40615-2", "9780306406157"),
        ("1-84356-028-3", "9781843560289"),
        ("0-8044-2957-X", "9780804429573"),
    ],
)
def test_canonical_isbn(isbn, expected):
    assert expected == str(CanonicalISBN(isbn))


@pytest.mark.parametrize(
    "isbn, expected",
    [
        ("978-000-000-000-X", "9780000000002"),
        ("978-000-000-001-X", "9780000000019"),
        ("978-000-000-002-X", "9780000000026"),
    ],
)
def test_fix_canonical_isbn(isbn, expected):
    assert expected == str(CanonicalISBN(isbn).fix())


def test_fix_returns_self_when_already_fixed():
    canonical = CanonicalISBN("9780000000002")
    assert canonical.fix() is canonical


@pytest.mark.parametrize(
    "isbn, expected",
    [
        ("978000000000X", 978000000000),
    ],
)
def test_canonical_isbn_to_isbn12(isbn, expected):
    assert expected == CanonicalISBN(isbn).to_isbn12()


@pytest.mark.parametrize("value", [None, 1.5, [], b"9780000000002", {}])
def test_is_isbn_type_error(value):
    with pytest.raises(TypeError):
        is_isbn(value)


@pytest.mark.parametrize("value", [None, 1.5, [], b"9780000000002", {}])
def test_canonical_isbn_type_error(value):
    with pytest.raises(TypeError):
        CanonicalISBN(value)


@pytest.mark.parametrize(
    "isbn, expected",
    [
        (978_000_000_000, "9780000000002"),
        ("978-000-000-000-X", "978000000000X"),
        ("978-000-000-000-3", "9780000000003"),
    ],
)
def test_normalize(isbn, expected):
    assert expected == str(normalize(isbn))


@pytest.mark.parametrize("value", [None, 1.5, [], b"9780000000002", {}])
def test_normalize_type_error(value):
    with pytest.raises(TypeError):
        normalize(value)


@pytest.mark.parametrize(
    "isbn, expected",
    [
        ("978-000-000-000-X", "9780000000002"),
        ("978-000-000-000-3", "9780000000002"),
    ],
)
def test_normalize_and_fix(isbn, expected):
    assert expected == str(normalize(isbn, fix=True))


@pytest.mark.parametrize(
    "isbn, layout_dict",
    [
        (
            "9780000000002",
            {
                "bookland": "978",
                "group": "0",
                "registrant": "00",
                "publication": "000000",
                "check_digit": "2",
            },
        ),
    ],
)
def test_isbn_layout_from_canonical(isbn, layout_dict):
    expected = ISBNLayout(**layout_dict)
    assert expected == ISBNLayout.from_canonical(CanonicalISBN(isbn))


def test_layout():
    canonical = CanonicalISBN("9780000000002")
    assert canonical.layout == ISBNLayout.from_canonical(canonical)
    assert canonical.layout is canonical.layout


@pytest.mark.parametrize(
    "isbn, expected",
    [
        ("9780000000002", "978-0-00-000000-2"),
    ],
)
def test_hyphenate_isbn(isbn, expected):
    assert expected == CanonicalISBN(isbn).hyphenate()


@pytest.mark.parametrize(
    "isbn, expected",
    [
        ("9780000000002", "978-0-00-000000-2"),
        ("978-000-000-000-X", "978-0-00-000000-2"),
        ("978-000-000-000-3", "978-0-00-000000-2"),
        (978_000_000_000, "978-0-00-000000-2"),
    ],
)
def test_pretty(isbn, expected):
    assert expected == pretty(isbn)


@pytest.mark.parametrize("value", [None, 1.5, [], b"9780000000002", {}])
def test_pretty_type_error(value):
    with pytest.raises(TypeError):
        pretty(value)


@pytest.mark.parametrize(
    "isbn, expected",
    [
        # Correct ISBN
        ("978000000000X", ValidationResult()),
        # ISBN from the reserved '979-0' group
        ("979000000000X", ValidationResult((InvalidISBNReason.BAD_GROUP,))),
        # ISBN from the undefined registrant range
        ("979800000000X", ValidationResult((InvalidISBNReason.BAD_REGISTRANT,))),
        # ISBN from the reserved group and with the incorrect check digit
        (
            "9790000000002",
            ValidationResult(
                (InvalidISBNReason.BAD_CHECK_DIGIT, InvalidISBNReason.BAD_GROUP),
            ),
        ),
    ],
)
def test_validate(isbn, expected):
    assert expected == CanonicalISBN(isbn).validate()


@pytest.mark.parametrize(
    "isbn, expected",
    [
        ("978000000000X", True),
        ("979000000000X", False),
        ("979800000000X", False),
        ("9790000000002", False),
    ],
)
def test_validate_bool(isbn, expected):
    assert expected == bool(CanonicalISBN(isbn).validate())


@pytest.mark.parametrize(
    "start_isbn, limit, expected",
    [
        (None, None, ["9780000000002", "9780000000019", "9780000000026"]),
        (978_000_000_003, 3, ["9780000000033", "9780000000040", "9780000000057"]),
        (979_999_999_999, 0, []),
        (979_999_999_999, 1, ["9799999999990"]),
        (979_999_999_999, 2, ["9799999999990"]),
    ],
)
def test_generate_isbns(start_isbn, limit, expected):
    if limit is None:
        testing_generator = islice(generate_isbns(start_isbn), 3)
    else:
        testing_generator = generate_isbns(start_isbn, limit)
    expected_values = [CanonicalISBN._from_normalized(x) for x in expected]
    assert expected_values == list(testing_generator)


@pytest.mark.parametrize("start_isbn", [978_000_000_000 - 1, 979_999_999_999 + 1])
def test_generate_isbns_outside(start_isbn):
    with pytest.raises(ValueError):
        next(generate_isbns(start_isbn))
