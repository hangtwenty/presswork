# -*- coding: utf-8 -*-
""" throw your strings to CleanInputString and "ensure" they have been sanitized, such as removing control characters.

CleanInputString will avoid running redundantly, by checking type of the input (good for Very Big Strings)

at the time of writing there are two cleaning filters in use:

    - remove all control characters besides newlines/CRLF (leave those) (remove null bytes etc)
    - "massage" inputs so that even if they have invalid, mixed encodings, we still coerce to Unicode
        with minimal information lost

to add other filter format_functions, just add format_functions to SANITIZERS filter list.

(exploratory testing yielded undesirable behavior when feeding in null bytes and so on.)

Lastly... There *is* some redundant processing on input and output; *some* is necessary, *some* is a shim.
I went down some ratholes trying to keep it only-the-necessary, but it was diminishing returns.
I'll revisit some of this if I'm ever in a "regex mood" or "unicode mood" ... and contributions welcome :)

more info & doctests below
"""
import logging
import re
from UserString import UserString

from bs4 import UnicodeDammit

logger = logging.getLogger("presswork")


# noinspection PyMissingConstructor
class CleanInputString(UserString):
    """ cleans up string upon input - unless it's already been cleaned!

    CleanInputString will avoid running redundantly, by checking type of the input and not re-cleaning if
    it's already this type. So no content has to be checked. (good for Very Big Strings)

    What 'clean' means here - *not* 'clean' in any security related sense.
    Rather, 'clean' for tokenization - and so, clean for training models.

    All tokenizers I have tried - will behave badly with punctuation they don't understand.
    For example, assume we are using a tokenizer that doesn't try to expand contractoins.
    Even so, it may tokenize "don't" to ["don't"] -- but "don’t" (curly apostrophe) to ["don", "’", "t"].
    When you end up training a model on that, then generating text from that ... you get cruft.

    Aside from that case, we also want to make sure we can keep most Unicode, even if input has mixed encodings
    (can't be choosy with found text!). Then while we're at it, we can get rid of extra null bytes etc too.

        >>> assert CleanInputString(u"hello") == u"hello"
        >>> assert isinstance(u"hello", unicode)
        >>> assert not CleanInputString("")  # confirm truthiness is same as normal strings
        >>> assert not CleanInputString(u"")  # confirm truthiness is same as normal strings
        >>> assert CleanInputString("hello")
        >>> null_byte = chr(0)
        >>> assert null_byte
        >>> assert null_byte != ''
        >>> assert CleanInputString(null_byte) == ''
        >>> assert CleanInputString(null_byte + "hello") == "hello"
        >>> assert CleanInputString(
        ... CleanInputString(CleanInputString(CleanInputString(u'idempotent')))) == u'idempotent'
        >>> cleaned = CleanInputString('hi')
        >>> # confirm we avoid redundant cleaning: we would expect the internal string to be exact same object
        >>> assert cleaned.data is CleanInputString(CleanInputString(CleanInputString(cleaned))).data
        >>> assert unicode(CleanInputString(u"unicøde")) == u"unicøde"
    """

    def __init__(self, s, cleaner_functions=None):
        # no call to super() is needed in this case: override is intentional.

        self.cleaner_functions = cleaner_functions or (
            unicode_dammit,
            lambda s: remove_control_characters(s, keep_newlines=True),
        )

        if simplify_quotes in self.cleaner_functions:
            # I hate having to put this here, but I went down a total rat-hole trying to figure out what had broken,
            # debugging every cleaner, tokenizer, and helper; failures in the test suite, no matter what.
            # Finally tried turning this off *on the input*, and it was OK. Maddens me that I don't know why yet!
            logger.warning(u"WARNING: Calling simplify_quotes on the input is considered iffy. Can cause some "
                           u"real head-scratcher bugs. YMMV.")

        if isinstance(s, CleanInputString):
            self.data = s.data
        else:
            s = self._clean(s)
            self.data = s

    def _clean(self, text):
        for clean in self.cleaner_functions:
            text = clean(text)
        return text

    def unwrap(self):
        """ return internal string (useful when we need to pass to something that is over-strict about type-checking)
        """
        return unicode(self.data)

    def __unicode__(self):
        return unicode(self.data)


class OutputProofreader(object):
    """ final massaging of string before display; its concern should only be "proofreading typos" kind of changes.

    this should only be used for final touchups to the text before display.
    (*nothing* fancy here - fancy things should be done to the Sentences and Word-Lists, and/or done by the Joiners.
    this should be a "dumb" final formatting step.)

    >>> text = b'weird ``quotes” fixed floating ' ' punct gets ) deleted -- keep “dashes" though'.decode('utf8')
    >>> print OutputProofreader().proofread(text)
    weird "quotes" fixed floating  punct gets  deleted -- keep "dashes" though
    """

    def __init__(self, cleaner_functions=None):
        self.cleaner_functions = cleaner_functions or (
            simplify_quotes,
            remove_floating_punctuation,
        )

    def proofread(self, text):
        for clean in self.cleaner_functions:
            text = clean(text)
        return text


_floating_punctuation_to_remove = """!"#$%&'()*+,.:;<=>?@[]^_`{}~"""
re_floating_ascii_punctuation = re.compile(
        u'(?<=\s)([%s])(?=\s)' % re.escape(_floating_punctuation_to_remove),
        flags=re.UNICODE)


def remove_floating_punctuation(text):
    """ Delete single characters of "floating" ASCII punctuation, with some exceptions.

    The regex is the source of truth here so for exactly which ones are kept/removed, see there

    (I went down a rathole trying to remove the _need_ to do this, before finally deciding that it is good enough
    for the purposes of this project today. It may be worth revisiting: remove it, see if there's a better way)

    >>> remove_floating_punctuation(u"hello ' I'm pleased   ' '  to meet ( and greet ) you (really, really !) ! ) ")
    u"hello  I'm pleased      to meet  and greet  you (really, really !)   "
    >>> remove_floating_punctuation(u"hello - I'm pleased -- ' '  to meet you. / know you")
    u"hello - I'm pleased --    to meet you. / know you"
    """
    return re_floating_ascii_punctuation.sub(u"", text)


_all_control_char_numbers = range(0, 32) + range(127, 160)
_char_numbers_besides_newlines = [c for c in _all_control_char_numbers if c not in (ord("\n"), ord('\n'))]
all_control_chars = map(unichr, _all_control_char_numbers)
control_chars_besides_newlines = map(unichr, _char_numbers_besides_newlines)

re_control_chars = re.compile(u'[%s]' % re.escape(u''.join(all_control_chars)), flags=re.UNICODE)
re_control_chars_besides_newlines = \
    re.compile(u'[%s]' % re.escape(u''.join(control_chars_besides_newlines)), flags=re.UNICODE)


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
    """ using bs4.UnicodeDammit, "coerce" text to unicode. replaces (some) 'smart quotes'. fixes (some) mixed encodings

    What's it do under the hood? The docs explain some, the source explains even more of course.
    https://www.crummy.com/software/BeautifulSoup/bs4/doc/#unicode-dammit

        >>> with_smart_quotes = b"I just \x93love\x94 your word processor\x92s smart quotes"
        >>> assert unicode_dammit(with_smart_quotes) == 'I just "love" your word processor\\'s smart quotes'

    :param override_encodings: why these defaults - in short, they are commonly seen in input texts I've played with.
        whether they are mixed or not. someday-maybe this can be configured with better control if needed.
    """

    cleaned = UnicodeDammit(s, smart_quotes_to=smart_quotes_to, override_encodings=override_encodings).unicode_markup
    return cleaned


def simplify_quotes(text):
    """ Even though UnicodeDammit smart_quotes_to="ascii" takes care of many cases, some crap can still be left...

    In addition to the smart-quotes, on *output* we also want to catch the case of `` -> " and '' -> "
    (NLTK has some tokenizers that convert like that).

    So, this can be used in the input cleaners chain, AFTER UnicodeDammit; it can also be used from OutputProofreader.

        >>> text = b'Have some ``weird" “quotes” and curlies,”  won’t you please. Quotes are ‘fun’'.decode('utf8')
        >>> print simplify_quotes(text)
        Have some "weird" "quotes" and curlies,"  won't you please. Quotes are 'fun'
        >>> print simplify_quotes(unichr(8220) + u"foo" + unichr(8221) + unichr(8216) + u"bar" + unichr(8217))
        "foo"'bar'
        >>> text = b'``weird" “quotes” aren’t very ‘fun’ I don’t think'.decode('utf8')
        >>> print simplify_quotes(text)
        "weird" "quotes" aren't very 'fun' I don't think
    """
    return (text
            .replace(u"``", u'"')
            .replace(u"''", u'"')
            .replace(u'“', u'"')
            .replace(u'”', u'"')
            .replace(u'’', u"'")
            .replace(u'‘', u"'"))
