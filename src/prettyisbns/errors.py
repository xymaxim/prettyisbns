"""Exceptions specific to the package."""

from __future__ import annotations

from enum import StrEnum, auto
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    import sys

    if "sphinx.ext.autodoc" in sys.modules:
        from prettyisbns.isbn import CanonicalISBN, MaybeISBN


class PrettyISBNsError(Exception):
    """Base package exception."""


class InvalidISBNReason(StrEnum):
    """Reasons for invalid ISBNs.

    Examples:
        While '978-0-00-000000-K' contains the bad check digit ('K'), we first
        don't recognize it as an ISBN with :func:`~prettyisbns.isbn.is_isbn`,
        and therefore :attr:`~InvalidISBNReason.NOT_ISBN` should be used
        here. Such reasons (along with bad length, bad characters, etc.) could
        be taken out into a separate enum, say, ``NotISBNReason``, but we don't
        go that far.
    """

    #: Not an ISBN.
    NOT_ISBN = auto()
    #: Undefined registration group.
    BAD_GROUP = auto()
    #: Undefined registrant.
    BAD_REGISTRANT = auto()
    #: Incorrectly calculated check digit.
    BAD_CHECK_DIGIT = auto()


class InvalidISBNError(PrettyISBNsError, ValueError):
    """Raised when an ISBN is not valid."""

    def __init__(
        self,
        message: str,
        reason: InvalidISBNReason,
        isbn: MaybeISBN | CanonicalISBN,
    ):
        """Creates an exception with ``message`` and ``reason`` for ``isbn``."""
        super().__init__(message)
        self.message = message
        self.reason = reason
        self.isbn = isbn

        self.add_note(f"\nISBN: '{self.isbn}'")

    def __str__(self) -> str:
        return f"{self.reason}: {self.message}"


class NotISBNError(InvalidISBNError):
    """Raised when the value is not an ISBN."""

    def __init__(self, isbn: MaybeISBN, message: str | None = None):
        """Creates an exception with ``message`` for ``isbn``."""
        message = message or "value is neither ISBN-10 nor ISBN-13"
        super().__init__(message, InvalidISBNReason.NOT_ISBN, isbn)

    def __str__(self) -> str:
        return self.message


class UndefinedISBNRangeError(InvalidISBNError):
    """Raised when the registration group or registrant range are undefined."""

    def __init__(self, message: str, reason: InvalidISBNReason, isbn: CanonicalISBN):
        """Creates an exception with ``message`` and ``reason`` for ``isbn``."""
        super().__init__(message, reason, isbn)

        self.add_note(
            "\nNote: this may be caused by outdated range data. "
            "Make sure that the range is defined for use at "
            "https://www.isbn-international.org/range_file_generation. "
            "If it is, update the package. "
            "If the error persists, please open an issue.",
        )


class NotISBN12Error(PrettyISBNsError, ValueError):
    """Raised when a value is not an ISBN-12 number."""
