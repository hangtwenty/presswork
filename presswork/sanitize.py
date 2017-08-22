""" throw your strings to SanitizedString and "ensure" they have been sanitized, such as removing control characters.

SanitizedString will avoid running redundantly, by checking type of the input (good for Very Big Strings)

    >>> hello = SanitizedString(chr(0) + "hello")
    >>> assert hello == "hello"
    >>> assert chr(0) not in hello
    >>> assert SanitizedString(hello) == hello

at time of writing there is only one sanitization filter in use:
remove all control characters besides newlines and carriage returns. (remove null bytes etc.)
other filter functions could be added, as needed, to SANITIZERS.

(exploratory testing yielded undesirable behavior when feeding in null bytes and so on.)

more info & doctests below
"""

import re
from UserString import UserString

_all_control_char_numbers = range(0, 32) + range(127, 160)
_char_numbers_besides_newlines = [c for c in _all_control_char_numbers if c not in (ord("\n"), ord('\n'))]
all_control_chars = map(unichr, _all_control_char_numbers)
control_chars_besides_newlines = map(unichr, _char_numbers_besides_newlines)

re_control_chars = re.compile('[%s]' % re.escape(''.join(all_control_chars)))
re_control_chars_besides_newlines = re.compile('[%s]' % re.escape(''.join(control_chars_besides_newlines)))


def remove_control_characters(string_or_unicode, keep_newlines=False):
    """ remove control characters regardless of whether they are ASCII or unicode

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

    :param string_or_unicode:
    :return:
    """
    if keep_newlines:
        return re_control_chars_besides_newlines.sub(u'', string_or_unicode)
    else:
        return re_control_chars.sub(u'', string_or_unicode)


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
        >>> # when avoiding redundant sanitization, we would expect the internal string to be exact same object
        >>> assert SanitizedString(SanitizedString(hi_san)).data is hi_san.data
    """

    SANITIZERS = (
        lambda s: remove_control_characters(s, keep_newlines=True),
    )

    def __init__(self, string):
        if isinstance(string, SanitizedString):
            self.data = string.data
        else:
            for sanitizer in self.SANITIZERS:
                string = sanitizer(string)
            self.data = string

    def __unicode__(self):
        return unicode(self.data)
