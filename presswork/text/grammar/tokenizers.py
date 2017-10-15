# -*- coding: utf-8 -*-
""" SentenceTokenizers, WordTokenizers - from unstructured text, to a tokenized structure

-------------------------------------------------------------------------------
design notes -- SentenceTokenizers, WordTokenizers
===============================================================================

    * These are collaborators: Each SentenceTokenizer has its own default WordTokenizer, but can be customized.
    * SentenceTokenizer takes in one string, tokenizes to sentences, then calls a WordTokenizer on each sentence
    * WordTokenizer takes in a list of strings (sentence-strings) and tokenizes each. (to 'words'.)
    * I starting writing an interface that seemed intuitive to me, then realized it is not so different from NLTK.
        I'll take that as affirmation that it makes basic sense, but I am going to keep a key difference -
        here I want to keep sentence and word tokenizations separate. defer flattening until last step when
        you are de-tokenizing/rejoining. then one can still iterate and filter over the list structures
        in various different ways, before re-joining to text (which is really a 'display' or 'frontend' concern).

"""
import logging

import markovify
import nltk
from nltk.tokenize.casual import TweetTokenizer

from presswork.text import clean
from presswork.text.grammar.containers import SentencesAsWordLists, WordList

logger = logging.getLogger('presswork')


class BaseWordTokenizer(object):
    """ base class for word tokenizer(s). (basic word-tokenizing ~= "splitting", but nuanced strategies exist too)
    """

    def __init__(self):
        self.strategy = None

    def tokenize(self, text):
        """ take string/unicode, split/tokenize into words, return list-of-words.
        :type text: basestring
        :rtype: presswork.text.grammar.containers.WordList
        """
        raise NotImplementedError()

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)


class BaseSentenceTokenizer(object):
    """ base class for sentence tokenizer(text); biased towards SentencesAsWordLists.
    """

    def __init__(self, word_tokenizer):
        self._word_tokenizer = None
        self.word_tokenizer = word_tokenizer
        self.strategy = None

    def tokenize(self, text):
        """ take string/unicode, tokenize into list-of-lists: [ [word, word, ...], [word, word, ...], ... ]
        :rtype: presswork.text.grammar.containers.SentencesAsWordLists
        """
        sentences = [self.word_tokenizer.tokenize(sentence) for sentence in self._tokenize_to_sentence_strings(text)]
        return SentencesAsWordLists(sentences)

    def _tokenize_to_sentence_strings(self, text):
        """ take string/unicode, tokenize into sentence-strings, return list of strings where each is a 'sentence'

        (this shouldn't depend on word_tokenizer)
        :rtype: list
        """
        raise NotImplementedError()

    @property
    def word_tokenizer(self):
        """
        >>> import pytest
        >>> with pytest.raises(ValueError): BaseSentenceTokenizer(word_tokenizer=None).word_tokenizer.tokenize()
        """
        if not self._word_tokenizer:
            raise ValueError("word_tokenizer not configured!")
        return self._word_tokenizer

    @word_tokenizer.setter
    def word_tokenizer(self, word_tokenizer):
        self._word_tokenizer = word_tokenizer

    def __repr__(self):
        return "{}(word_tokenizer={!r})".format(self.__class__.__name__, self.word_tokenizer)


class WordTokenizerWhitespace(BaseWordTokenizer):
    """ crude - basically just wraps split() (splits on all whitespace), just presenting in same interface.
    """

    def tokenize(self, text):
        """
            >>> newline = chr(10)
            >>> tuple(WordTokenizerWhitespace().tokenize("foo bar baz" + newline * 10 + " quux " + newline * 20000))
            ('foo', 'bar', 'baz', 'quux')
        """
        return WordList(text.split())


class SentenceTokenizerWhitespace(BaseSentenceTokenizer):
    """ crude - similar to string.splitlines(), maybe handles a couple other edge cases. Backed by regex.

    Default pairing - WordTokenizerWhitespace (tokenize both sentences & words on whitespace)

    http://www.nltk.org/api/nltk.tokenize.html
    """

    def __init__(self, word_tokenizer=None):
        if word_tokenizer is None:
            word_tokenizer = WordTokenizerWhitespace()
        super(SentenceTokenizerWhitespace, self).__init__(word_tokenizer)
        self.strategy = nltk.BlanklineTokenizer()

    def _tokenize_to_sentence_strings(self, text):
        """
            >>> newline = chr(10)
            >>> list(SentenceTokenizerWhitespace()._tokenize_to_sentence_strings(2 * ("x" + newline + "y" + newline)))
            ['x', 'y', 'x', 'y']
        """
        return text.splitlines()


class SentenceTokenizerMarkovify(BaseSentenceTokenizer):
    """ Markovify has its own 'sentence splitter' using regexes, it's like Whitespace one with a little more oomph.

    Default pairing - WordTokenizerWhitespace, of course.

    https://github.com/jsvine/markovify/blob/v0.6.0/markovify/splitters.py#L41-L53
    """

    def __init__(self, word_tokenizer=None):
        if not word_tokenizer:
            word_tokenizer = WordTokenizerWhitespace()
        super(SentenceTokenizerMarkovify, self).__init__(word_tokenizer)

    def _tokenize_to_sentence_strings(self, text):
        text = clean.CleanInputString(text).unwrap()
        return markovify.splitters.split_into_sentences(text)


class WordTokenizerNLTK(BaseWordTokenizer):
    """ uses an NLTK tokenizer to tokenize a sentence into words.

    When re-joining/de-tokenizing, this works best with JoinerNLTK.

    Why the "TweetTokenizer"? NLTK's recommended word tokenizer as of 3.2.4 is Treebank, and I started with that,
    and sustained for a while. But I couldn't get it to stop tokenizing contractions ("don't" -> "do n't"),
    even when it seemed like I configured it right. The tokenizing of contractions has its uses in NLP in general,
    but in our context here, it's not very useful, and presents big pains for testing.
    TweetTokenizer is a good compromise, and it's actually pretty general purpose, despite its tongue-in-cheek name.

    http://www.nltk.org/api/nltk.tokenize.html
    http://text-processing.com/demo/tokenize/
    """

    def __init__(self):
        super(WordTokenizerNLTK, self).__init__()

        self.strategy = TweetTokenizer(preserve_case=True, reduce_len=False, strip_handles=False)

    def tokenize(self, text):
        """
            >>> WordTokenizerNLTK().tokenize("It's a beautiful day today...")
            [u"It's", u'a', u'beautiful', u'day', u'today', u'...']
            >>> from presswork.text.clean import CleanInputString
            >>> WordTokenizerNLTK().tokenize(CleanInputString("Hello there!!!"))
            [u'Hello', u'there', u'!', u'!', u'!']
        """
        text = clean.CleanInputString(text).unwrap()
        return WordList(self.strategy.tokenize(text))


class SentenceTokenizerNLTK(BaseSentenceTokenizer):
    """ uses NLTK's "Punkt" to tokenize sentences. (NLTK's recommended sentence tokenizer as of 3.2.4 is Punkt.)

    Default pairing - WordTokenizerNLTK (the other NLTK 1st-recommended tokenizer, but for words.)

    When re-joining/de-tokenizing, this works best with JoinerNLTK

    http://www.nltk.org/api/nltk.tokenize.html
    http://text-processing.com/demo/tokenize/
    """

    def __init__(self, word_tokenizer=None):
        if not word_tokenizer:
            word_tokenizer = WordTokenizerNLTK()

        super(SentenceTokenizerNLTK, self).__init__(word_tokenizer)

        # Punkt Sentence Tokenizer has a pretty funny "constructor", indeed... you just load a pickle.
        self.strategy = nltk.data.load('tokenizers/punkt/english.pickle')

    def _tokenize_to_sentence_strings(self, text):
        text = clean.CleanInputString(text).unwrap()
        return self.strategy.tokenize(text)


# ===============================================================

tokenizer_classes_by_nickname = {
    "nltk": SentenceTokenizerNLTK,
    "just_whitespace": SentenceTokenizerWhitespace,
    "markovify": SentenceTokenizerMarkovify
}

TOKENIZER_NICKNAMES = tokenizer_classes_by_nickname.keys()


def create_sentence_tokenizer(nickname):
    return tokenizer_classes_by_nickname[nickname]()
