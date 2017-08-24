# -*- coding: utf-8 -*-
""" containers for sentences-of-words, plus Splitter/Tokenizer and Rejoiner utilities & strategies

-------------------------------------------------------------------------------
design notes -- overall, contrast with similar libs, & context in project
===============================================================================

    * (to start with,) this module mostly just fronts other libs and modules, but helps with clean/uniform usage
    * most common flow for text generator play: text => structured model (=> generate) => rejoin to text
    * more concretely: text => tokenize to sentences (& token sentences to words) (=> generate) => rejoin to text
    * essential data structure is list-of-words: a sentence is just a list-of-words.
    * this is similar to NLTK's view of things, and Markovify's view of things. with some differences:
        * the main diff. vs. NLTK: NLTK likes flat list of words (some methods flatten sentence structure too eagerly)
        * the main diff. vs. Markovify: Markovify uses the Sentences-As-Word-Lists structure too,
            but then stringifies a bit eagerly.
    * by keeping more structure and being more 'lazy' about rejoining, we can mix-and-match more strategies.

-------------------------------------------------------------------------------
design notes -- WordTokenizers, SentenceTokenizers
===============================================================================

    * these take in strings and tokenize ('parse') out to lists of sentences, lists of words
    * sentence tokenizer tokenizes to sentences & tokenizes each sentence to words.
    * keep these minimal, basically method-objects, with a unified interface
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
        or plain lists-of-lists. don't type-check and depend on the type of these.
    * if helper methods are added to them, they should be just that - HELPERS - i.e. things should work OK
        without them. just 'guardrails' or 'progressive enhancements', if that makes sense.

-------------------------------------------------------------------------------
design notes -- Joiners
===============================================================================

    * a Joiner takes in SentencesAsWordLists and joins the tokens back into strings according to some strategy.
    * so it is the same responsibility as a 'de-tokenizer' as NLTK calls it. but calling it a Joiner to keep it broad.
        I imagine weirder things a Joiner could do, not just "de-tokenizing", but putting in variations as it goes -
        whitespace/indentation, enjambment, etc., as they re-join. Could be good for (pseudo-)poetic uses

"""
import logging
import re
import string
from UserList import UserList

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
        raise NotImplementedError()

    def __call__(self, *args, **kwargs):
        return self.tokenize(*args, **kwargs)

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)


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
        raise NotImplementedError()

    @property
    def word_tokenizer(self):
        if not self._word_tokenizer:
            raise ValueError("word_tokenizer not configured!")
        return self._word_tokenizer

    @word_tokenizer.setter
    def word_tokenizer(self, word_tokenizer):
        self._word_tokenizer = word_tokenizer

    def __call__(self, *args, **kwargs):
        return self.tokenize(*args, **kwargs)

    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)


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

    Default pairing - WordTokenizerWhitespace, of course.

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


class WordTokenizerTreebank(BaseWordTokenizer):
    """ uses nltk.TreebankWordTokenizer for words. (NLTK's recommended word tokenizer as of 3.2.4 is Treebank.)

    http://www.nltk.org/api/nltk.tokenize.html
    """

    def __init__(self):
        super(WordTokenizerTreebank, self).__init__()
        self.strategy = nltk.TreebankWordTokenizer()

    def tokenize(self, text):
        if not isinstance(text, SanitizedString) and not isinstance(text, unicode):
            logger.warning("NLTK expects unicode, but this text is type={}".format(type(text)))
        return WordList(self.strategy.tokenize(unicode(text)))


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
        if not isinstance(text, SanitizedString) and not isinstance(text, unicode):
            logger.warning("NLTK expects unicode, but this text is type={}".format(type(text)))
        return self.strategy.tokenize(unicode(text))


# # #TODO
# # class MarkovifySentenceTokenizer(BaseSentenceTokenizer):
# #     """ markovify has its own 'sentence splitter' using regexes, might as well have it as an option
# #       https://github.com/jsvine/markovify/blob/master/markovify/splitters.py#L41-L53
# #     """
# #     def _tokenize_to_sentence_strings(self, text):
# #         return crude_split_sentences(text)
#
#
#
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

    def sanity_check(self):
        if self.data:
            if not isinstance(self.data[0], basestring):
                raise ValueError("should be list of strings")


class SentencesAsWordLists(UserList):
    """ basically a list of lists of strings, with helper methods that make sense for 'sentences'
    """

    def __init__(self, seq):
        super(SentencesAsWordLists, self).__init__(seq)
        self.sanity_check()

    def sanity_check(self):
        if self.data:
            if isinstance(self.data[0], basestring):
                raise ValueError("should be list of lists, appears to be list of strings")


# TODO delete this method
# @DeprecationWarning
def crude_split_sentences(text):
    """ do basic split-up of 'sentences' returning tuple.
    """
    return tuple(SentenceTokenizerWhitespace()._tokenize_to_sentence_strings(text))


# TODO delete this method
# @DeprecationWarning
def crude_split_words(text):
    """ do basic split-up of words, returning tuple

        >>> newline = chr(10)
        >>> crude_split_words("foo bar baz" + newline * 10 + " quux " + newline * 20000)
        ('foo', 'bar', 'baz', 'quux')
    """
    return tuple(text.split())


# FIXME delete this method, should be using Joiners
# TODO(hangtwenty) rejoiner aka composer classes... but still keep a convenience-function that's just like "rejoin it the default way" yet
def rejoin(sentences_of_words, sentence_sep="\n", word_sep=" "):
    return sentence_sep.join(word_sep.join(word for word in sentence) for sentence in sentences_of_words)


# ===============================================================

# alias these since they are "NLTK recommended," and  outside of this module, caller shouldn't have to think about
# subtleties of NLTK recommending (Punkt combined with Treebank)
WordTokenizerNLTK = WordTokenizerTreebank
SentenceTokenizerNLTK = SentenceTokenizerPunkt

tokenizer_classes_by_nickname = {
    "nltk": SentenceTokenizerNLTK,
    "whitespace": SentenceTokenizerWhitespace
}


def create_sentence_tokenizer(nickname):
    return tokenizer_classes_by_nickname[nickname]()
