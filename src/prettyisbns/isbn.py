"""Classes and functions to work with ISBNs."""

from __future__ import annotations

import re

from dataclasses import asdict, dataclass
from functools import cached_property
from re import Pattern
from typing import TYPE_CHECKING, Final, Literal, NamedTuple, Self, cast

from prettyisbns.errors import (
    InvalidISBNError,
    InvalidISBNReason,
    NotISBN12Error,
    NotISBNError,
    UndefinedISBNRangeError,
)
from prettyisbns.ranges import REGISTRANT_RANGES, REGISTRATION_GROUPS


if TYPE_CHECKING:
    import sys

    if "sphinx.ext.autodoc" in sys.modules:
        from collections.abc import Generator

# Type aliases

#: A valid ISBN-12 integer number.
type ISBN12 = int

#: A string that is expected to be an ISBN.
type MaybeISBN = str

BooklandElement = Literal["978", "979"]

# Constants

#: A simple pattern to match ISBN-10 and ISBN-13 values.
ISBN_PATTERN: Pattern[str] = re.compile(r"^(?:978|979)?\d{9}[\dXx]$")

#: First defined ISBN-12.
FIRST_ISBN: Final[ISBN12] = 978_000_000_000

#: Last defined ISBN-12.
LAST_ISBN: Final[ISBN12] = 979_999_999_999

#: Total number of ISBNs.
TOTAL_ISBNS: Final = LAST_ISBN - FIRST_ISBN + 1

#: The length of ISBN-12 numbers.
ISBN12_LENGTH = 12


class ISBNBounds(NamedTuple):
    """Represents ISBN bounds."""

    start: ISBN12
    end: ISBN12


@dataclass(frozen=True)
class ValidationResult:
    """Represents the result of validating an ISBN."""

    #: Reasons for failed checks.
    errors: tuple[InvalidISBNReason, ...] = ()

    def __bool__(self) -> bool:
        return not self.errors


class CanonicalISBN:
    """Represents a canonical (normalized) ISBN-13 string.

    The canonical form is a 13-digit ISBN string without hyphens or whitespace.
    ISBN-10 and hyphenated input values are normalized to this form upon
    creation.

    Only the ISBN-10 and ISBN-13 :data:`pattern <ISBN_PATTERN>` check is
    performed upon creation. So canonical ISBN values are assumed to be valid
    even if: the registration group or registrant range are undefined, the
    correct digit is incorrectly calculated. For validation, see
    :meth:`validate`.

    See Also:
        :func:`normalize`
    """

    def __init__(self, value: MaybeISBN):
        """Creates a canonical ISBN-13 object."""
        self._value = self._normalize_value(value)

    @classmethod
    def _from_normalized(cls, isbn: str) -> Self:
        """Creates a new object from an already normalized ISBN-13 string."""
        new = cls.__new__(cls)
        new._value = isbn
        return new

    def _normalize_value(self, value: MaybeISBN) -> str:
        # Remove dashes and whitespaces
        output_value = _clean_isbn_string(value)

        # Check if value is ISBN-10 or ISBN-13
        if not is_isbn(output_value):
            raise NotISBNError(value)

        # Convert ISBN-10 to ISBN-13 if needed, recomputing the check digit
        if len(output_value) == 10:
            isbn12_value = f"978{output_value[:9]}"
            output_value = f"{isbn12_value}{_calculate_check_digit(int(isbn12_value))}"

        # Ensure that the 'X' check digit is uppercase
        if output_value[-1] == "x":
            output_value = output_value.upper()

        return output_value

    @property
    def bookland(self) -> BooklandElement:
        """Returns the bookland element."""
        return self._value[:3]  # type: ignore[return-value]

    @property
    def check_digit(self) -> str:
        """Returns the check digit."""
        return self._value[-1]

    @cached_property
    def layout(self) -> ISBNLayout:
        """Splits the ISBN into its elements.

        Raises:
            InvalidISBNError: If the registration group or registrant range is
                undefined.
        """
        return ISBNLayout.from_canonical(self)

    def fix(self) -> Self:
        """Fixes the ISBN with the correct check digit."""
        correct_check_digit = _calculate_check_digit(self)
        if self.check_digit == str(correct_check_digit):
            return self
        return self._from_normalized(f"{self._value[:-1]}{correct_check_digit}")

    def hyphenate(self) -> str:
        """Returns the hyphenated ISBN string.

        Raises:
            InvalidISBNError: If the registration group or registrant range is
                undefined.
        """
        return self.layout.hyphenate()

    def validate(self) -> ValidationResult:
        """Validates the ISBN: its check digit, registration group, and registrant.

        Returns:
            A :class:`ValidationResult` with the errors for failed checks as
            :class:`~prettyisbns.errors.InvalidISBNReason` members.
        """
        errors: list[InvalidISBNReason] = []

        if self.check_digit.isnumeric() and self.check_digit != str(
            _calculate_check_digit(self),
        ):
            errors.append(InvalidISBNReason.BAD_CHECK_DIGIT)

        try:
            _ = self.layout
        except InvalidISBNError as error:
            errors.append(error.reason)

        return ValidationResult(tuple(errors))

    def to_isbn12(self) -> ISBN12:
        """Converts to an :data:`ISBN12` number."""
        return int(self._value[:ISBN12_LENGTH])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __getitem__(self, key: int | slice) -> str:
        return self._value[key]

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value})"


@dataclass(frozen=True)
class ISBNLayout:
    """Represents the layout of an ISBN-13 string.

    Note:
        Registration group and registrant ranges used for the layout were
        periodically updated from the RangeMessage.xml file available from the
        International ISBN Agency and may not be the most recent.

    Example:
        It is more practical to create it from a canonical ISBN:
          >>> canonical = normalize("978-000-000-000-X")
          >>> ISBNLayout.from_canonical(canonical)
          ISBNLayout(
              bookland='978',
              group='0',
              registrant='00',
              publication='000000',
              check_digit='X',
          )

        You can slice to get full prefixes:
          # Get the registrant prefix
          >>> ISBNLayout.from_canonical(canonical)[:3]
          '978-0-00'
    """

    #: Bookland, or GS1 element.
    bookland: BooklandElement
    #: Registration group element.
    group: str
    #: Registrant element.
    registrant: str
    #: Publication element.
    publication: str
    #: Check digit.
    check_digit: str

    @classmethod
    def from_canonical(cls, isbn: CanonicalISBN) -> Self:
        """Splits a canonical ISBN-13 into its elements.

        Raises:
            InvalidISBNError: If the registration group or registrant range is
                undefined.
        """
        max_registrant_length = 7

        bookland = isbn.bookland
        current_index = len(bookland)

        # Extract a registration group element
        group_prefix = _extract_group_prefix(isbn)
        _, group = group_prefix.split("-")
        current_index += len(group)

        # Match a registrant element
        isbn_rest_part = isbn[current_index:]
        registrant_ranges = REGISTRANT_RANGES[group_prefix]
        for range_start, range_end, registrant_length in registrant_ranges:
            registrant_probe = isbn_rest_part[:max_registrant_length]
            # For some groups (e.g., '978-99998'), the length of ISBN-13 may not
            # be enough to get the probe
            registrant_probe = registrant_probe.ljust(max_registrant_length, "0")
            if range_start <= registrant_probe <= range_end:
                if registrant_length == 0:
                    message = (
                        "not defined for use registrant: "
                        f"'{group_prefix}-{registrant_probe}'"
                    )
                    raise UndefinedISBNRangeError(
                        message,
                        InvalidISBNReason.BAD_REGISTRANT,
                        isbn,
                    )
                registrant = isbn_rest_part[:registrant_length]
                current_index += registrant_length
                break
        else:
            raise UndefinedISBNRangeError(
                f"invalid (or unknown) registrant: {group_prefix}",
                InvalidISBNReason.BAD_REGISTRANT,
                isbn,
            )

        return cls(
            bookland=bookland,
            group=group,
            registrant=registrant,
            publication=isbn[current_index:-1],
            check_digit=isbn.check_digit,
        )

    @property
    def _elements(self) -> dict[str, str | BooklandElement]:
        return asdict(self)

    def hyphenate(self) -> str:
        """Formats an ISBN string with elements delimited by a hyphen."""
        return "-".join(self._elements.values())

    def __getitem__(self, key: int | slice[int, int, None]) -> str:
        match key:
            case slice() as x if x.step is not None:
                raise ValueError("slice step is not supported")
            case slice() as x:
                return "-".join(list(self._elements.values())[x])
            case int() as index:
                return list(self._elements.values())[index]
            case _:
                raise TypeError("index must be integer or slice object")


def _clean_isbn_string(x: MaybeISBN) -> MaybeISBN:
    if not isinstance(x, str):
        raise TypeError(f"value must be str, got {type(x)}")
    return x.replace("-", "").replace(" ", "")


def ensure_isbn12(value: int) -> ISBN12:
    """Ensures that a value is an ISBN-12 number."""
    if not isinstance(value, int):
        raise TypeError(f"value must be int, got {type(value)}")
    if not (FIRST_ISBN <= value <= LAST_ISBN):
        raise NotISBN12Error(
            f"value must be in range [{FIRST_ISBN}, {LAST_ISBN}], got {value}",
        )
    return value


def _calculate_check_digit(isbn: CanonicalISBN | ISBN12) -> int:
    """Calculates the check digit for an ISBN."""
    isbn_value = str(isbn)[:ISBN12_LENGTH]
    total = 0
    for i in range(len(isbn_value)):
        digit = int(isbn_value[i])
        if i % 2 == 0:
            total += digit
        else:
            total += digit * 3
    return (10 - (total % 10)) % 10


def normalize(value: MaybeISBN | ISBN12, fix: bool = False) -> CanonicalISBN:
    """Normalizes an ISBN to a canonical ISBN-13 string without hyphens.

    Arguments:
        value: An ISBN-10, ISBN-13, or ISBN-12 value to normalize.
        fix: Whether to replace an incorrect or 'X' check digit with the correct
            one. Defaults to `False`.

    Returns:
        The canonical ISBN.

    Raises:
        NotISBNError: If the value is neither an ISBN-10 nor an ISBN-13.
        NotISBN12Error: If an integer value is outside the ISBN-12 range.

    See Also:
        :func:`pretty`, a shortcut, which returns the hyphenated form.

    Examples:
        1) The input ISBN-13 string with the correct check digit:

          >>> normalize("978-000-000-000-2")
          CanonicalISBN(9780000000002)

        2) The input ISBN-13 string with the incorrect check digit:

          >>> # Keep it as it is
          >>> normalize("978-000-000-000-3")
          CanonicalISBN(9780000000003)

          >>> # Or, correct the check digit
          >>> normalize("978-000-000-000-3", fix=True)
          CanonicalISBN(9780000000002)

        3) The input ISBN-13 string with the 'X' check digit:

          >>> # Keep it as it is
          >>> normalize("978-000-000-000-X")
          CanonicalISBN(978000000000X)

          >>> # Or, replace the 'X' with the correct check digit
          >>> normalize("978-000-000-000-X", fix=True)
          CanonicalISBN(9780000000002)

        4) The input :data:`ISBN12` integer value:

          >>> value: ISBN12 = 978_000_000_000
          >>> normalize(value)
          CanonicalISBN(9780000000002)
    """
    match value:
        case int():
            isbn12 = ensure_isbn12(value)
            normalized_isbn = CanonicalISBN._from_normalized(f"{isbn12}X").fix()
        case str():
            normalized_isbn = CanonicalISBN(cast("str", value))
            if fix:
                normalized_isbn = normalized_isbn.fix()
        case _:
            raise TypeError(f"value must be str or int, got {type(value)}")
    return normalized_isbn


def pretty(value: MaybeISBN | ISBN12) -> str:
    """Returns the ISBN with the correct check digit and hyphens.

    This is a shortcut for ``normalize(value, fix=True).hyphenate()``.

    Arguments:
        value: An ISBN-10, ISBN-13, or ISBN-12 value to format.

    Returns:
        The hyphenated ISBN-13 string.

    Raises:
        NotISBNError: If the value is neither an ISBN-10 nor an ISBN-13.
        NotISBN12Error: If an integer value is outside the ISBN-12 range.
        InvalidISBNError: If the registration group or registrant range is
            undefined.

    See Also:
        :func:`normalize`, which returns the canonical form without hyphens.

    Examples:
        >>> pretty("978-000-000-000-X")
        '978-0-00-000000-2'
    """
    return normalize(value, fix=True).hyphenate()


def is_isbn(x: MaybeISBN) -> bool:
    """Checks that the input string is an ISBN-10 or ISBN-13."""
    return bool(re.match(ISBN_PATTERN, _clean_isbn_string(x)))


def get_prefix_bounds(prefix: str) -> ISBNBounds:
    """Gets bounds for an ISBN prefix."""
    prefix = prefix.replace("-", "")
    return ISBNBounds(
        start=int(prefix.ljust(ISBN12_LENGTH, "0")),
        end=int(prefix.ljust(ISBN12_LENGTH, "9")),
    )


def get_prefix_capacity(prefix: str) -> int:
    """Gets the capacity of an ISBN prefix."""
    return 10 ** (ISBN12_LENGTH - len(prefix.replace("-", "")))


def _extract_group_prefix(isbn: CanonicalISBN) -> str:
    """Extracts the group prefix from the ISBN.

    Arguments:
        isbn: A canonical ISBN-13 string.

    Returns:
        A found full ISBN group prefix, e.g. '978-1'.

    Raises:
        :class:`~prettyisbns.errors.InvalidISBNError`: If the ISBN does not contain
            valid group prefix.

    See Also:
        :class:`ISBNLayout`
    """
    bookland_length = 3
    max_group_length = 5

    isbn_string = str(isbn)

    group_prefix = ""
    for group_length in range(1, max_group_length + 1):
        group = isbn_string[bookland_length : bookland_length + group_length]
        group_prefix = f"{isbn_string[:bookland_length]}-{group}"
        if group_prefix in REGISTRATION_GROUPS:
            break
    else:
        raise UndefinedISBNRangeError(
            f"invalid (or unknown) registration group: {group_prefix}",
            InvalidISBNReason.BAD_GROUP,
            isbn,
        )

    return group_prefix


def generate_isbns(
    start_isbn: ISBN12 | None = None,
    limit: int | None = None,
) -> Generator[CanonicalISBN]:
    """Yields canonical ISBN-13 string values.

    Arguments:
        start_isbn: A start ISBN-12 number. Defaults to `None`, meaning yields
            from the first ISBN-13, '978-000-000-000-2'.
        limit: A maximum number of ISBNs to yields. Defaults to `None`, meaning
            yields till the last ISBN-13, '979-999-999-999-0'.

    """
    if start_isbn is None:
        start_isbn = FIRST_ISBN
    start_isbn = int(start_isbn)

    if not (FIRST_ISBN <= start_isbn <= LAST_ISBN):
        raise ValueError(
            f"start value must be in range [{FIRST_ISBN:_d}, {LAST_ISBN:_d}], "
            f"got {start_isbn:_d}",
        )

    if limit is not None:
        end_isbn: ISBN12 = start_isbn + limit - 1
        end_isbn = min(end_isbn, LAST_ISBN)
    else:
        end_isbn = LAST_ISBN

    for isbn in range(int(start_isbn), int(end_isbn) + 1):
        yield normalize(isbn)
