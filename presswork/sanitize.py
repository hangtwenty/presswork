# -*- coding: utf-8 -*-
""" throw your strings to SanitizedString and "ensure" they have been sanitized, such as removing control characters.

SanitizedString will avoid running redundantly, by checking type of the input (good for Very Big Strings)

at the time of writing there are two sanitization filters in use:

    - remove all control characters besides newlines/CRLF (leave those) (remove null bytes etc)
    - "massage" inputs so that even if they have invalid, mixed encodings, we still coerce to Unicode
        with minimal information lost

to add other filter functions, just add functions to SANITIZERS filter list.

(exploratory testing yielded undesirable behavior when feeding in null bytes and so on.)

more info & doctests below
"""

import re
from UserString import UserString

from bs4 import UnicodeDammit

_all_control_char_numbers = range(0, 32) + range(127, 160)
_char_numbers_besides_newlines = [c for c in _all_control_char_numbers if c not in (ord("\n"), ord('\n'))]
all_control_chars = map(unichr, _all_control_char_numbers)
control_chars_besides_newlines = map(unichr, _char_numbers_besides_newlines)

re_control_chars = re.compile(u'[%s]' % re.escape(u''.join(all_control_chars)), flags=re.UNICODE)
re_control_chars_besides_newlines = re.compile(u'[%s]' % re.escape(u''.join(control_chars_besides_newlines)), flags=re.UNICODE)


class SanitizedString(UserString):
    """ sanitizes string upon input - unless it's already been sanitized.

    SanitizedString will avoid running redundantly, by checking type of the input (good for Very Big Strings)

        >>> assert SanitizedString(u"hello") == u"hello"
        >>> assert isinstance(u"hello", unicode)
        >>> assert not SanitizedString("")  # confirm truthiness is same as normal strings
        >>> assert not SanitizedString(u"")  # confirm truthiness is same as normal strings
        >>> assert SanitizedString("hello")
        >>> null_byte = chr(0)
        >>> assert null_byte
        >>> assert null_byte != ''
        >>> assert SanitizedString(null_byte) == ''
        >>> assert SanitizedString(null_byte + "hello") == "hello"
        >>> assert SanitizedString(SanitizedString(SanitizedString(SanitizedString(u'idempotent')))) == u'idempotent'
        >>> hi_san = SanitizedString('hi')
        >>> # confirm we avoid redundant sanitization: we would expect the internal string to be exact same object
        >>> assert SanitizedString(SanitizedString(hi_san)).data is hi_san.data
    """

    # noinspection PyMissingConstructor
    def __init__(self, s):
        # no call to super() is needed here; full override is intentional.
        if isinstance(s, SanitizedString):
            self.data = s.data[:]
        else:
            for sanitizer in SANITIZERS:
                s = sanitizer(s)
            self.data = s

    def __unicode__(self):
        return unicode(self.data)


def remove_control_characters(string_or_unicode, keep_newlines=False):
    """ remove control characters such as null bytes & others. optionally, retain newlines/CRLF.

    adapted solution from here, https://stackoverflow.com/a/93029/884640
    ... surprised there is no stdlib function for it, but this will do.

    some redundancy in this test but just to be thorough as well as obvious...
    ... it does repeat the definition of control_chars basically for example, but that is intentional

        >>> import random, sys
        >>> null_byte = chr(0)
        >>> basic_input = "hello" + null_byte + "world"
        >>> assert null_byte in basic_input
        >>> assert null_byte not in remove_control_characters(basic_input)
        >>> all_chars = (unichr(i) for i in xrange(sys.maxunicode))
        >>> all_chars_as_list = list(all_chars)
        >>> random.shuffle(all_chars_as_list)
        >>> all_chars_shuffled = "".join(all_chars_as_list)
        >>> del all_chars, all_chars_as_list
        >>> all_chars_except_control_chars = remove_control_characters(all_chars_shuffled)
        >>> assert null_byte not in all_chars_except_control_chars
        >>> control_char_nums = range(0, 32) + range(127, 160)
        >>> for character in map(unichr, control_char_nums):
        ...     assert character not in all_chars_except_control_chars
        >>> newline = chr(10)  # (using chr(10) because putting literal newline in doctest/docstring messes it up)
        >>> x = remove_control_characters(newline + "hello" + null_byte + newline, keep_newlines=True)
        >>> assert x == newline + "hello" + newline
        >>> x = remove_control_characters(newline + "hello" + null_byte + newline, keep_newlines=False)
        >>> assert x == "hello"

    """
    if keep_newlines:
        return re_control_chars_besides_newlines.sub(u'', string_or_unicode)
    else:
        return re_control_chars.sub(u'', string_or_unicode)


def unicode_dammit(s, override_encodings=('utf-8', 'windows-1252', 'iso-8859-1', 'latin-1'), smart_quotes_to="ascii"):
    """ using UnicodeDammit, "coerce" text to unicode. for example will replace 'smart quotes'. it's the lesser evil!

    just a wrapper around UnicodeDammit that sets defaults arguments/calls that make sense for current known uses.
    but it will forward other **kwargs if given.

    UnicodeDammit docs say exactly what it does: https://www.crummy.com/software/BeautifulSoup/bs4/doc/#unicode-dammit

    can be destructive and drop characters that are incorrectly encoded. however it's the LEAST destructive option.
    but we accept that tradeoff to take more input... without getting "mojibake" (nonsense from mixed encodings)

        >>> with_smart_quotes = b"I just \x93love\x94 your word processor\x92s smart quotes"
        >>> assert unicode_dammit(with_smart_quotes) == 'I just "love" your word processor\\'s smart quotes'

    Overrall UnicodeDammit is the right tool for the job, given the options available; where "the job" is to
    try and preserve as much unicode as we can instead of limiting ourselves to ASCII... but not break on mixed
    incodings. Inputs will often come from The Internet where they can be very messy. Even Project Gutenberg texts
    are often messy with mixed encodings. So we accept the tradeoff of a somewhat difficult dependency, for benefit
    of having Unicode and mixed-encoding support from very early on in this project.

    Caveats: Mainly, it's a complicated dependency to manage, unless we make some changes both upstream & downstream.

        (a) UnicodeDammit only ships with BeautifulSoup4 - that's a Bunch of Stuff we don't need.
        (b) UnicodeDammit has a nice feature of progressive-enhancing to use `cchardet` or `chardet` if installed.
        unfortunately this cannot be turned off, and at time of writing, `chardet` is proving very slow, and `cchardet`
        has over-sensitive type checking that rejects valid inputs.

    TODO: file github issue about "revisiting unicode approach" that can have some ideas for both (a) and (b).
    TODO( issue += ) : a destructive fallback option: https://pypi.python.org/pypi/Unidecode
    (less destructive than .decode(errors='ignore'), but still pretty destructive; reduces to ASCII.)

    :param override_encodings: why these defaults - in short, they are commonly seen in input texts I've played with.
        whether they are mixed or not. someday-maybe this can be configured with better control if needed.
    """

    cleaned = UnicodeDammit(s, smart_quotes_to="ascii", override_encodings=override_encodings).unicode_markup
    return cleaned


SANITIZERS = (
    unicode_dammit,
    lambda s: remove_control_characters(s, keep_newlines=True),
)
