Usage
#####

.. contents:: Contents
   :depth: 1
   :backlinks: top
   :local:

Normalize input values
**********************

Suppose we have an ISBN and want to make it pretty:

.. code-block:: python

   isbn = "978-23-6590-117-X"

It might be hyphenated (correctly or not), end with an 'X' or an incorrect
check digit, or not be an ISBN at all.

First, let's normalize it with :func:`~prettyisbns.isbn.normalize`:

.. code-block:: pycon

   >>> from prettyisbns import normalize

   # Normalize the ISBN, keep the 'X' check digit
   >>> canonical = normalize(isbn)
   >>> canonical
   CanonicalISBN(978236590117X)

The result is a :class:`~prettyisbns.isbn.CanonicalISBN`, a stripped ISBN-13
string.

Next, let's fix it with the correct check digit, replacing the 'X':

.. code-block:: python

   >>> canonical.fix()
   CanonicalISBN(9782365901178)

   # Or normalize and correct it in one step
   >>> normalize(isbn, fix=True)
   CanonicalISBN(9782365901178)

Now our value is a well-formed ISBN-13 with a correct check digit.

We can then, for example, convert it to an ISBN-12 integer:

.. code-block:: pycon

   >>> isbn12 = canonical.to_isbn12()
   >>> isbn12
   978236590117

Match input values
******************

If the input value is not an ISBN,
:class:`~prettyisbns.errors.NotISBNError` is raised:

.. code-block:: python

   >>> normalize("not isbn")
   prettyisbns.errors.NotISBNError: value is neither ISBN-10 nor ISBN-13

   Problematic ISBN: 'not isbn'

If you only need to check whether a value is an ISBN-10 or ISBN-13, without
normalizing it, use :func:`~prettyisbns.isbn.is_isbn`:

.. code-block:: pycon

   >>> from prettyisbns.isbn import is_isbn
   >>> is_isbn("9780000000002") and is_isbn("0-00-000000-2")
   True
   >>> is_isbn("not isbn")
   False

Format ISBNs
************

Canonical ISBNs can be formatted with hyphens separating their elements:

.. code-block:: pycon

   >>> canonical.hyphenate()
   '978-2-36590-117-8'

Now that looks pretty!

To normalize, fix, and format in one step, use :func:`~prettyisbns.pretty`, a
shortcut for ``normalize(value, fix=True).hyphenate()``:

.. code-block:: pycon

   >>> from prettyisbns import pretty
   >>> pretty('978236590117X')
   '978-2-36590-117-8'

Internally, this is done by the :class:`~prettyisbns.isbn.ISBNLayout` class,
which validates ISBN ranges and splits ISBNs into distinct elements. In most
cases you do not need to instantiate it directly. It is available through the
:attr:`~prettyisbns.isbn.CanonicalISBN.layout` property. The layout is created
on first access and cached:

.. code-block:: pycon

   >>> canonical.layout
   ISBNLayout(
       bookland='978',
       group='2',
       registrant='36590',
       publication='117',
       check_digit='8',
   )

With the layout, we can also split an ISBN into prefixes by slicing it:

.. code-block:: pycon

   # Get the full registrant prefix
   >>> canonical.layout[:3]
   '978-2-36590'

Validate ISBNs
**************

Normalizing an ISBN with :func:`~prettyisbns.isbn.normalize` does not tell
us whether the ISBN is valid or why it is not. For that, use the
:meth:`~prettyisbns.isbn.CanonicalISBN.validate` method:

.. code-block:: pycon

   >>> result = normalize("978000000000-9").validate()
   >>> result
   ValidationResult(errors=(<InvalidISBNReason.BAD_CHECK_DIGIT: 'bad_check_digit'>,))

   >>> if not result:
   >>> ... print(f"Invalid: {result.errors}")
   (<InvalidISBNReason.BAD_CHECK_DIGIT: 'bad_check_digit'>,)


In addition to checking the check digit,
:meth:`~prettyisbns.isbn.CanonicalISBN.validate` checks the registration group
and the registrant range, and stores errors for failed checks as members of
:attr:`~prettyisbns.errors.InvalidISBNReason`.

.. code-block:: pycon

   # Bad check digit and registration group
   >>> normalize("978990000000-9").validate().errors
   (<InvalidISBNReason.BAD_CHECK_DIGIT: 'bad_check_digit'>,
    <InvalidISBNReason.BAD_GROUP: 'bad_group'>)

   # Bad registrant
   >>> normalize("9789999800006").validate().errors
   (<InvalidISBNReason.BAD_REGISTRANT: 'bad_registrant'>,)

Registration groups and registrant ranges
*****************************************

As you may have noticed, the formatted ISBN differs from our initial input
(978-23-6590-117-X), which was formatted incorrectly. Splitting an ISBN into
elements requires knowing the valid registration groups and registrant
ranges. These ranges are published on the `International ISBN Agency
<https://www.isbn-international.org/>`__ website, and we store them in the
auto-generated :mod:`prettyisbns.ranges` module.

.. note::

   The ranges may change over time. Until the module is updated, newly
   defined ranges are considered invalid. If a defined range is still not
   recognized after updating the package, please open an issue.

Work with ISBN-12 values
************************

There is no such thing as an ISBN-12: ISBNs are either ISBN-10 or ISBN-13. In
this package, *ISBN-12* is the name for an ISBN-13 without its check digit,
represented as an integer. The check digit can always be calculated from the
other digits, so nothing is lost. And since an ISBN-13 always starts with 978
or 979, no leading zeros are dropped.

.. code-block:: pycon

   >>> canonical.to_isbn12()
   978236590117

Since :func:`~prettyisbns.isbn.normalize` also accepts ISBN-12 values, you
can do arithmetic with them, for example, to get the next ISBN:

.. code-block:: pycon

   >>> next_isbn = normalize(canonical.to_isbn12() + 1)
   >>> next_isbn.hyphenate()
   '978-2-36590-118-5'

For another usage of ISBN-12 values, see `allisbns
<https://github.com/xymaxim/allisbns>`__.

Summary
*******

To get a pretty ISBN from an input value, normalize it with the check digit
corrected, and then format it. Both steps can fail, so it is a good idea to
handle the errors:

.. code-block:: python

   from prettyisbns import normalize
   from prettyisbns.errors import InvalidISBNError, NotISBNError

   try:
       # Normalize and fix the check digit
       canonical = normalize("978-23-6590-117-X", fix=True)
       # Format
       pretty = canonical.hyphenate()
   except NotISBNError:
       ...
   except InvalidISBNError as error:
       print(f"Cannot be formatted: {error.reason}")
   else:
       print(pretty)  # 978-2-36590-117-8

The ``reason`` attribute of :class:`~prettyisbns.errors.InvalidISBNError` is an
:class:`~prettyisbns.errors.InvalidISBNReason` member, the same one that
:func:`~prettyisbns.isbn.CanonicalISBN.validate` returns in errors, except that
formatting stops at the first error.
