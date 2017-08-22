""" containers for sentences-of-words, plus Splitter and Rejoiner utilities & strategies
"""
import re


def crude_split_sentences(s):
    """ do basic split-up of 'sentences' returning tuple.

    splits based on newlines (TODO: also punctuation), without NLTK etc. (for crude/simple needs)

        >>> newline = chr(10)
        >>> crude_split_sentences(3 * ("foo" + newline + "bar" + newline))
        ('foo', 'bar', 'foo', 'bar', 'foo', 'bar')
        >>> # TODO test - TODO should split on <punctuation-or-newline> actually...
    """
    # for now just splits on newlines, TODO should split on <punctuation-or-newline> actually...
    return tuple(s.splitlines())


def crude_split_words(s):
    """ do basic split-up of words, returning tuple

        >>> newline = chr(10)
        >>> crude_split_words("foo bar baz" + newline * 10 + " quux " + newline * 20000)
        ('foo', 'bar', 'baz', 'quux')
    """
    return tuple(s.split())
