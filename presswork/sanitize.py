""" throw your strings to SanitizedString and "ensure" they have been sanitized, such as removing control characters.

SanitizedString will avoid running redundantly, by checking type of the input (good for Very Big Strings)

    >>> hello = SanitizedString(chr(0) + "hello")
    >>> assert hello == "hello"
    >>> assert chr(0) not in hello
    >>> assert SanitizedString(hello) == hello

at time of writing there is only one sanitization filter in use, the removal of control characters like null etc.
other functions could be added, as needed, to SANITIZERS.

more info & doctests below
"""

import re
from UserString import UserString

control_chars = ''.join(map(unichr, range(0, 32) + range(127, 160)))
control_char_re = re.compile('[%s]' % re.escape(control_chars))


def remove_control_characters(string_or_unicode):
    """ remove control characters regardless of whether they are ASCII or unicode

    solution is from here, https://stackoverflow.com/a/93029/884640
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

    :param string_or_unicode:
    :return:
    """
    return control_char_re.sub('', string_or_unicode)


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
        remove_control_characters,
    )

    def __init__(self, string):
        if isinstance(string, SanitizedString):
            self.data = string.data
        else:
            for sanitizer in self.SANITIZERS:
                string = sanitizer(string)
            self.data = string

