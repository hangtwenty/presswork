# -*- coding: utf-8 -*-
""" containers for sentences-of-words, plus Splitter/Tokenizer and Rejoiner utilities & strategies

    >>> list(WordTokenizerWhitespace().tokenize('foo bar baz'))
    ['foo', 'bar', 'baz']
    >>> SentenceTokenizerNLTK().tokenize('Foo bar baz. Another sentence in the input.').unwrap()
    [['Foo', 'bar', 'baz', '.'], ['Another', 'sentence', 'in', 'the', 'input', '.']]
    >>> # TODO show the joiners too

------------------------------------------------------------------------------------
design notes -- high level/ context. & compare/contrast to approach in similar libs
====================================================================================

    * (to start with,) this module mostly just fronts other libs and modules, but helps with clean/uniform usage
    * most common flow for text generator play: text => structured model (=> generate) => rejoin to text
    * more concretely: text => tokenize to sentences (& token sentences to words) (=> generate) => rejoin to text
    * essential data structure is list-of-words: a sentence is just a list-of-words.
    * this is similar to NLTK's view of things, and Markovify's view of things. with some differences:
        * the main diff. vs. NLTK: NLTK likes flat list of words (some methods flatten sentence structure too eagerly)
        * the main diff. vs. Markovify: Markovify uses the Sentences-As-Word-Lists structure too,
            but then stringifies a bit eagerly (i.e. before returning anything, if you want to post-process
            you have to redundantly tokenize, and that can be lossy, messy).
    * by keeping more structure and being more 'lazy' about rejoining, we can mix-and-match more strategies.

-------------------------------------------------------------------------------
design notes -- WordTokenizers, SentenceTokenizers
===============================================================================

    * These are collaborators: Each SentenceTokenizer has its own default WordTokenizer, but can be customized.
    * WordTokenizer takes in a list of strings (sentence-strings) and tokenizes each. (to 'words'.)
    * SentenceTokenizer takes in one string, tokenizes to sentences, then calls a WordTokenizer on each sentence
    * I starting writing an interface that seemed intuitive to me, then realized it is not so different from NLTK.
        I'll take that as affirmation that it makes basic sense, but I am going to keep a key difference -
        here I want to keep sentence and word tokenizations separate. defer flattening until last step when
        you are de-tokenizing/rejoining. then one can still iterate and filter over the list structures
        in various different ways, before re-joining to text (which is really a 'display' or 'frontend' concern).

-------------------------------------------------------------------------------
design notes -- WordList, SentencesAsWordLists
===============================================================================

    * simple containers, maybe with some helper methods
        * [ [word, word, ...], [word, word, ...], ... ]
    * Keep duck-typing in mind - most things that use these, should also Just Work when given plain lists,
        or plain lists-of-lists. don't type-check strictly, stay compatible with primitives/builtins
    * if helper methods are added to them, they should be just that - HELPERS - i.e. things should work OK
        without them. just 'guardrails' or 'progressive enhancements', if that makes sense.

-------------------------------------------------------------------------------
design notes -- Joiners
===============================================================================

    * a Joiner takes in SentencesAsWordLists and joins the tokens back into strings according to some strategy.
    * so it is the same responsibility as a 'de-tokenizer' as NLTK calls it. but calling it a Joiner to keep it broad.
        I imagine weirder things a Joiner could do, not just "de-tokenizing", but putting in variations as it goes -
        whitespace/indentation, enjambment, etc., as they re-join. Could be good for (pseudo-)poetic uses!

"""
import logging
import re
import string
from UserList import UserList

import markovify
import nltk

from presswork.sanitize import SanitizedString

logger = logging.getLogger('presswork')

re_ascii_punctuation = re.compile(u'[%s]' % re.escape(string.punctuation), flags=re.UNICODE)


class BaseWordTokenizer(object):
    """ base class for word tokenizer(s). (basic word-tokenizing ~= "splitting", but nuanced strategies exist too)
    """

    def __init__(self):
        self.strategy = None

    def tokenize(self, text):
        """ take string/unicode, split/tokenize into words, return list-of-words.
        :type text: basestring
        :rtype: WordList
        """
        raise NotImplementedError()  # pragma: no cover

    def __repr__(self):  # pragma: no cover
        return "{}()".format(self.__class__.__name__)


class BaseSentenceTokenizer(object):
    """ base class for sentence tokenizer(text); biased towards SentencesAsWordLists.
    """

    def __init__(self, word_tokenizer):
        self.word_tokenizer = word_tokenizer
        self.strategy = None

    def tokenize(self, text):
        """ take string/unicode, tokenize into list-of-lists: [ [word, word, ...], [word, word, ...], ... ]
        :rtype: SentencesAsWordLists
        """
        sentences = [self.word_tokenizer.tokenize(sentence) for sentence in self._tokenize_to_sentence_strings(text)]
        return SentencesAsWordLists(sentences)

    def _tokenize_to_sentence_strings(self, text):
        """ take string/unicode, tokenize into sentence-strings, return list of strings where each is a 'sentence'

        (this shouldn't depend on word_tokenizer)
        :rtype: list
        """
        raise NotImplementedError()  # pragma: no cover

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

    def __repr__(self):  # pragma: no cover
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
        if hasattr(text, 'unwrap'):
            text = text.unwrap()
        return markovify.splitters.split_into_sentences(text)


class WordTokenizerTreebank(BaseWordTokenizer):
    """ uses nltk.TreebankWordTokenizer for words. (NLTK's recommended word tokenizer as of 3.2.4 is Treebank.)

    http://www.nltk.org/api/nltk.tokenize.html
    """

    def __init__(self):
        super(WordTokenizerTreebank, self).__init__()
        self.strategy = nltk.TreebankWordTokenizer()

    def tokenize(self, text):
        """
        >>> # just getting coverage for .unwrap() line, which doesn't end up exercised by other tests
        >>> WordTokenizerTreebank().tokenize(SanitizedString("Hello there!!!"))
        [u'Hello', u'there', u'!', u'!', u'!']
        """
        if hasattr(text, 'unwrap'):
            text = text.unwrap()
        return WordList(self.strategy.tokenize(text))


class SentenceTokenizerPunkt(BaseSentenceTokenizer):
    """ uses NLTK's "Punkt" to tokenize sentences. (NLTK's recommended sentence tokenizer as of 3.2.4 is Punkt.)

    Default pairing - WordTokenizerTreebank (the other NLTK 1st-recommended tokenizer, but for words.)

    http://www.nltk.org/api/nltk.tokenize.html
    """

    def __init__(self, word_tokenizer=None):
        if not word_tokenizer:
            word_tokenizer = WordTokenizerTreebank()

        super(SentenceTokenizerPunkt, self).__init__(word_tokenizer)

        # Punkt Sentence Tokenizer has a pretty funny "constructor", indeed... you just load a pickle.
        self.strategy = nltk.data.load('tokenizers/punkt/english.pickle')

    def _tokenize_to_sentence_strings(self, text):
        if hasattr(text, 'unwrap'):
            text = text.unwrap()
        return self.strategy.tokenize(text)



# class BaseJoiner(object):
#     # TODO need to decide on interface. Probably it just takes SentencesAsWordLists as sole argument, yeah?
#     pass
#
#
# class JoinerWhitespace(object):
#     # TODO it's just the crude existing rejoin() function, look for that
#     pass
#
#
# class JoinerMoses(object):
#     # TODO Moses Detokenizer!? http://www.nltk.org/api/nltk.tokenize.html
#     pass


class WordList(UserList):
    """ basically a list of strings, with helper methods that make sense for'words'
    """

    def __init__(self, seq):
        super(WordList, self).__init__(seq)
        self.sanity_check()

    def sanity_check(self):
        """
        >>> import pytest
        >>> assert WordList(["some", "words"])
        >>> with pytest.raises(ValueError): WordList([["oops", "you", "passed..."], ["a", "sentence", "list"]])
        """
        if self.data:
            if not isinstance(self.data[0], basestring):
                raise ValueError("should be list of strings")

    def unwrap(self):
        """ return internal list (useful when we need to pass to something that is over-strict about type-checking)
        """
        return self.data

class SentencesAsWordLists(UserList):
    """ basically a list of lists of strings, with helper methods that make sense for 'sentences'
    """

    def __init__(self, seq):
        super(SentencesAsWordLists, self).__init__(seq)
        self.sanity_check()

    def sanity_check(self):
        """
        >>> import pytest
        >>> assert SentencesAsWordLists([["oops", "you", "passed..."], ["a", "sentence", "list"]])
        >>> with pytest.raises(ValueError): SentencesAsWordLists(["oops", "it's", "a", "flat", "list", "of", "words"])
        >>> with pytest.raises(ValueError): WordList([["oops", "you", "passed..."], ["a", "sentence", "list"]])
        """
        if self.data:
            if isinstance(self.data[0], basestring):
                raise ValueError("should be list of lists, appears to be list of strings")

    def unwrap(self):
        """ return internal list (useful when we need to pass to something that is over-strict about type-checking)
        """
        try:
            # if self.data is a list of WordList instances, this will work
            return [word_list.unwrap() for word_list in self.data]
        except AttributeError:
            return [word_list for word_list in self.data]


# FIXME delete this method, should be using Joiners
# TODO(hangtwenty) rejoiner aka composer classes... but still keep a convenience-function that's just like "rejoin it the default way" yet
def rejoin(sentences_of_words, sentence_sep="\n", word_sep=" "):
    return sentence_sep.join(word_sep.join(word for word in sentence) for sentence in sentences_of_words).strip()


# ===============================================================

# alias these since they are "NLTK recommended," and  outside of this module, caller shouldn't have to think about
# subtleties of NLTK recommending (Punkt combined with Treebank)
WordTokenizerNLTK = WordTokenizerTreebank
SentenceTokenizerNLTK = SentenceTokenizerPunkt

tokenizer_classes_by_nickname = {
    "nltk": SentenceTokenizerNLTK,
    "whitespace": SentenceTokenizerWhitespace,
    "markovify": SentenceTokenizerMarkovify
}

TOKENIZER_NICKNAMES = tokenizer_classes_by_nickname.keys()


def create_sentence_tokenizer(nickname):
    return tokenizer_classes_by_nickname[nickname]()
