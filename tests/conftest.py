# -*- coding: utf-8 -*-
""" suite-wide fixtures.

some notes:
    - the plaintext fixtures:
        - there is some boilerplate to make it so none of the test cases have to 'know' much about this.
        they just name the fixture, and they get a string of source text
        - the plaintext ones are set up to start with 1+ of each type, but we can add more just by adding a file to
        each subdirectory, as needed
"""
import pytest

from . import fixtures


def pytest_runtest_setup(item):
    """ adds to pytest hooks - ensure logging gets set up (helpful when things fail)
    :param item: pytest `item`, not used in this case
    """

    # (memoizing this here *as well*; for normal use it's good to get a debug msg ack'ing redundant setup_logging call,
    # however when we are just making sure it has run before any given test (in this process), we just call each time,
    # and we really don't need the redundant warning messages)
    global _PRESSWORK_LOGGING_HAS_BEEN_SET_UP
    from presswork import log
    if not log.PRESSWORK_LOGGING_HAS_BEEN_SET_UP:
        log.setup_logging()


@pytest.fixture(params=[
    u'just_one_word',
    u'one two',
    u'\tbegin\t             \t\t   determ1 determ2 determ3 d4 d5 end',
    u'begin zzz1 zzz2 zzz3 zzz4 \t XYZ_0 XYZ_1 XYZ_2 XYZ_3 plus_ünicôde end',
])
def text_easy_deterministic(request):
    """ text inputs that parse to all-unique (no-duplicate) words; expect deterministic model (& easy test case)

    just outputs same sequence every time. this is a good basic way to smoketest parity, without getting into the
    more creative methods that work around probability (... and those creative tests themselves could get bugs etc ,
    so it helps: if simple case breaks too, you might go down a different debugging path.)
    """
    text_no_duplicate_words = request.param

    # choosing which sentence to start from is allowed to be random for the text makers. in other cases we might
    # seed or mock random, but here let's just eliminate the consideration, and use 1 'sentence' of input
    # (after all these cares are just supposed to be easy)
    assert "\n" not in text_no_duplicate_words and "\r" not in text_no_duplicate_words

    # sanity check - for these test inputs, there should be no duplicate words in the text
    _words = text_no_duplicate_words.split()
    assert len(_words) == len((set(_words)))

    return text_no_duplicate_words


class StrFromFilename(str):
    """ it's str() but it can have a filename attached. helps for fixtures; see example usage in test_cli.py

    *INTENTIONALLY* is str not unicode, as we want to leave it "raw" until our own code-under-test processes it.
    also, found that subclassing UserString was not a good fit - unrelated reason though: Click library's test helpers
    choked on it.

    (additionally it is not UserString because when it was UserString, something like Click CliRunner etc was
    rejecting it based on strict type-checking.)

    (example where this is relevant - see test_cli.py)
    """

    def __new__(cls, string):
        instance = super(StrFromFilename, cls).__new__(cls, string)
        instance.filename = None
        return instance

    @classmethod
    def load_from_filename(cls, filename):
        # attn: do *not* specify encoding here, we want to read it raw & pass it to code-under-test raw.
        with open(filename, 'r') as f:
            instance = cls(f.read())
        instance.filename = filename
        return instance


@pytest.fixture(params=fixtures.FILENAMES_NEWLINES)
def text_any(request):
    """ fixture returns 1 string, loaded from *any* of the plaintext file filxtures (1 at a time/ parametrized)
    """
    filename = request.param
    return StrFromFilename.load_from_filename(filename)


@pytest.fixture(params=fixtures.FILENAMES_NEWLINES)
def text_newlines(request):
    """ fixture returns 1 string, loaded from appropriate plaintext file (1 at a time/ parametrized)

    newlines ~= "mostly" newlines, actually - not purely
    """
    filename = request.param
    return StrFromFilename.load_from_filename(filename)


@pytest.fixture(params=fixtures.FILENAMES_PROSE)
def text_prose(request):
    """ fixture returns 1 string, loaded from appropriate plaintext file (1 at a time/ parametrized)
    """
    filename = request.param
    return StrFromFilename.load_from_filename(filename)


@pytest.fixture(params=fixtures.FILENAMES_MIXED)
def text_mixed(request):
    """ fixture returns 1 string, loaded from appropriate plaintext file (1 at a time/ parametrized)
    """
    filename = request.param
    return StrFromFilename.load_from_filename(filename)


@pytest.fixture(params=[
    "",
    " " * 9999,
    "\n",
    "\r",
    "\n\r",
    "\x20",
    "\x00",])
def empty_or_null_string(request):
    """

    I had a regression during early dev of `crude` where empty inputs were causing undefined behavior.
    These inputs helped ferret it out & proved the fix, so keeping them as regression tests.

    that should be tested closer to the unit that is at fault (tests for `crude`), but should be tested here too,
    as the CLI shouldn't panic or wait on an infinite loop in these cases. (regardless of impl details)
    :param runner:
    :return:
    """
    return request.param
