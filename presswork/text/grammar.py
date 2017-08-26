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
import random
import re
import string
from UserList import UserList

import markovify
import nltk
from nltk.tokenize.moses import MosesDetokenizer

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

    When re-joining/de-tokenizing, this works best with JoinerMoses

    http://www.nltk.org/api/nltk.tokenize.html
    """

    def __init__(self):
        super(WordTokenizerTreebank, self).__init__()
        self.strategy = nltk.TreebankWordTokenizer()

    def tokenize(self, text):
        """
        >>> # just getting coverage for .unwrap() line, which doesn't end up exercised by other tests
        >>> from presswork.sanitize import SanitizedString
        >>> WordTokenizerTreebank().tokenize(SanitizedString("Hello there!!!"))
        [u'Hello', u'there', u'!', u'!', u'!']
        """
        if hasattr(text, 'unwrap'):
            text = text.unwrap()
        return WordList(self.strategy.tokenize(text))


class SentenceTokenizerPunkt(BaseSentenceTokenizer):
    """ uses NLTK's "Punkt" to tokenize sentences. (NLTK's recommended sentence tokenizer as of 3.2.4 is Punkt.)

    Default pairing - WordTokenizerTreebank (the other NLTK 1st-recommended tokenizer, but for words.)

    When re-joining/de-tokenizing, this works best with JoinerMoses

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


class Joiner(object):
    """ given tokenized sentences and words, re-format for display. outputs a string (no markup etc.)

    >>> print Joiner(separate_sentences=". ").join([['Foo', 'bar', 'baz'], ['More', 'of', 'the', 'same']])
    Foo bar baz. More of the same
    >>> print Joiner(separate_sentences="/~   ", separate_words="   ").join([['How', 'are', 'U'], ['Not', 'bad']])
    How   are   U/~   Not   bad
    """

    def __init__(self, separate_sentences="\n", separate_words=" "):
        """
        :param separate_sentences: (if not empty) put this between sentences (specifically, before each sentence)
        :param separate_words: (if not empty) put this between words (specifically, after each word)

        The input tokenized text might have its own sentence punctuation, so it depends on your text,
        whether you want separate_sentences="", separate_sentences=". ", separate_sentences="<newline>". Experiment!
        """
        self._sentence_separator = separate_sentences
        self._word_separator = separate_words

        # explicitly declaring stateless by default. however, subclasses are free to be stateful
        self._state = None

    def join(self, sentences_as_word_lists):
        """ just wraps ._join_sentences(), adding a sanity check beforehand.

        >>> import pytest
        >>> with pytest.raises(ValueError): Joiner().join('wrong_data_structure')
        >>> with pytest.raises(ValueError): Joiner().join(['wrong_data_structure'])
        >>> joiner = Joiner(separate_sentences=" | ")
        >>> print joiner.join([['this', 'is', 'the'], ['expected', 'data', 'structure']])
        this is the | expected data structure
        >>> assert joiner.join([[]]) == ""
        >>> assert joiner.join([[""]]) == ""
        """
        if sentences_as_word_lists:
            sentences_as_word_lists = SentencesAsWordLists.ensure(sentences_as_word_lists)
        return self._join_sentences(sentences_as_word_lists)

    def _join_sentences(self, sentences_as_word_lists):
        """  takes SentencesAsWordLists and "re-joins" or "de-tokenizes" into a string.

        :param sentences_as_word_lists: Should typically be a SentencesAsWordLists instance, but builtins of the same
            structure are A-OK.
        :type sentences_as_word_lists: SentencesAsWordLists
        :rtype: basestring
        """
        if sentences_as_word_lists:
            if len(sentences_as_word_lists) > 1:
                result = self._join_words(sentences_as_word_lists[0]) + u"".join(
                        (self.between_sentences() or u"") + self._join_words(sentence)
                        for sentence in sentences_as_word_lists[1:]
                )
            else:
                result = self._join_words(sentences_as_word_lists[0])
        else:
            result = u""
        return result.strip()

    def _join_words(self, word_list):
        # calls between_sentences() in between each - while this is extra calls for some joiner strategies,
        # overall it keeps things maximally flexible: between_sentences() can be overridden to return dynamic values
        if word_list:
            if len(word_list) > 1:
                return u"".join(
                        word + (self.between_words() or u"") for word in word_list[:-1]) + word_list[-1]
            else:
                return word_list[0]
        else:
            return u""

    def between_sentences(self):
        """ for most subclasses: just return self._sentence_separator. However, quirky weird Joiners can override.
        """
        # TODO(->github-issues) Someday/Maybe it would be good to make this take argument (prev, current, next)
        # so it could have context-sensitive logic!!!
        return self._sentence_separator

    def between_words(self):
        """ for most subclasses: just return self._word_separator. However, quirky weird Joiners can override.
        """
        # TODO(->github-issues) Someday/Maybe it would be good to make this take argument (prev, current, next)
        # so it could have context-sensitive logic!!!
        return self._word_separator


class JoinerWhitespace(Joiner):
    """ Just hardcodes to newlines and spaces (regardless of whether the base class is using the same defaults)

        >>> print JoinerWhitespace().join([['foo', 'bar', 'baz'], ['quux']])
        foo bar baz
        quux
    """

    def __init__(self, separate_sentences="\n", separate_words=" "):
        super(JoinerWhitespace, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words)


class JoinerMoses(Joiner):
    """ Wraps NLTK's Moses De-tokenizer. This is NLTK's recommended de-tokenizer.

    NOTE: Whenever using NLTK's *tokenizers* (Punkt, Treebank) it is best to put through *this* strategy,
    as those tokenizers separate punctuation out. That separation is good for markov-model-training,
    but bad for display if left alone ("Lots of this . Extra paces ."). MosesDetokenizer handles it well.

    http://www.nltk.org/api/nltk.tokenize.html

    >>> joiner = JoinerMoses(separate_sentences=" ")
    >>> print joiner.join([['Foo', 'bar', 'baz', '.'], ['More', 'of', 'the', 'same.']])
    Foo bar baz. More of the same.
    >>> print joiner.join([['How', 'do', 'you', 'do', '?'], ['Fine,', 'you', '?']])
    How do you do? Fine, you?
    >>> assert joiner.join([[]]) == ""
    >>> assert joiner.join([[""]]) == ""
    """

    def __init__(self, separate_sentences="\n", separate_words=" ", lang="en"):
        """
        :param lang: Passed to MosesDetokenizer, which supports various languages (see docs).
        """
        super(JoinerMoses, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words)
        self._moses_detokenizer = MosesDetokenizer(lang=lang)

    def _join_words(self, word_list):
        # passing to moses detokenizer is simple ...
        sentence_string = self._moses_detokenizer.detokenize(word_list, return_str=True)

        # ... but in our terms, MosesDetokenizer assumes separate_words=" ". That's OK in some case,
        # but we want it so other separators can be passed in; AND so that the between_words() hook is still respected.
        # ... but to also respect custom word separator hook, we re-split & send to self._join_words
        sentence_string = super(JoinerMoses, self)._join_words(word_list=sentence_string.split())

        return sentence_string


class JoinerMosesWithRandomIndent(Joiner):
    """ want crude pseudopoetry? just add pseudorandom indentation! Default is (0-8)*2spaces.

        >>> joiner = JoinerMosesWithRandomIndent(_random=random.Random(456))
        >>> print joiner.join([["Expect", "some", "intense"], ["Indents."]] * 3)
        Expect some intense
                    Indents.
                        Expect some intense
              Indents.
                      Expect some intense
                  Indents.
        >>> print joiner.join([["Random", "runs"], ["How", "fun"]])
        Random runs
                  How fun
        >>> assert joiner.join([[]]) == ""
        >>> assert joiner.join([[""]]) == ""
    """

    def __init__(self, separate_sentences="\n", separate_words=" ", _random=None):
        """
        :param _random: can pass in random.Random(...) (i.e. random with seed)
        """
        super(JoinerMosesWithRandomIndent, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words)
        if _random:
            self.random = _random
        else:
            self.random = random.random()

        self.indent_unit = (separate_words or u"") * 2

    def _random_indent(self):
        """ newline + 0-8 * (2 spaces). i.e. default: {0, 2 ... 16} spaces
        """
        separator = (self.indent_unit) * self.random.randint(0, 8)
        return separator

    def between_sentences(self):
        return self._sentence_separator + self._random_indent()


class JoinerMosesWithRandomEnjambment(JoinerMosesWithRandomIndent):
    """ want funkier pseudopoetry? don't just indent, enjamb! in addition to indenting, breaks sentences

        >>> joiner = JoinerMosesWithRandomEnjambment(_random=random.Random(50))
        >>> # note, the <BLANKLINE> below is a doctest thing, in real output it would be real blank line
        >>> print joiner.join([["Expect", "some", "intense"], ["Indents", "and", "enjamb-", "ments"]])
        Expect some
        <BLANKLINE>
            intense
                Indents and
        <BLANKLINE>
                    enjamb-
        <BLANKLINE>
                      ments
        >>> joiner = JoinerMosesWithRandomEnjambment(_random=random.Random(3))
        >>> print joiner.join([["Random", "runs"], ["How", "fun,", "how", "fun", "&", "done"]])
        Random
        <BLANKLINE>
              runs
                  How fun,
        <BLANKLINE>
                      how
        <BLANKLINE>
                        fun & done
        >>> assert joiner.join([[]]) == ""
        >>> assert joiner.join([[""]]) == ""
    """

    def __init__(self, separate_sentences="\n", separate_words=" ", _random=None):
        super(JoinerMosesWithRandomEnjambment, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words, _random=_random)

        self.enjambment_chance = 0.33
        self.enjambment_extra_line_break_choices = [2, 2, 2, 4]

    def between_words(self):
        """ achieves 'enjambment' by breaking sentences - inserting newlines & indents between 'words' too
        :return:
        """
        if self.random.random() < self.enjambment_chance:
            maybe_newline = self._sentence_separator * self.random.choice(self.enjambment_extra_line_break_choices)
            return maybe_newline + self._random_indent().lstrip(self._sentence_separator)
        else:
            return self._word_separator


re_closing_punctuation_preceded_by_space = re.compile(r'\s([!"\'%),-./:;?]|}~](?:\s|$))', flags=re.UNICODE)


class StringProofreader(object):
    """ final massaging of string before display. keep this dumb, only for last fixups.

    This regex definitely isn't a cure-all for iffy formatting, maybe that's possible, for now I just want *something*

    >>> print StringProofreader().format("Some tokenizer+joiner combos leave space around periods . Let 's fix that !")
    Some tokenizer+joiner combos leave space around periods. Let's fix that!
    >>> print StringProofreader().format('text . . . is fun : very , very fun !! ! yada: yada blah ; hi')
    text... is fun: very, very fun!!! yada: yada blah; hi
    """

    def __init__(self, format_functions=None):
        if format_functions:
            self.format_functions = format_functions
        else:
            self.format_functions = [
                self._remove_spaces_before_closing_punctuation,
            ]

    def format(self, string):
        for function in self.format_functions:
            string = function(string)
        return string

    def _remove_spaces_before_closing_punctuation(self, string):
        """ Replace " . " with ". ", and so on, for other punctuation that probably ends sentences
        or clauses.
        """
        return re.sub(re_closing_punctuation_preceded_by_space, r'\1', string)


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
        >>> from presswork import sanitize
        >>> assert WordList([sanitize.SanitizedString("yee")])
        """
        if self.data:
            first_value = self.data[0]
            if (not isinstance(first_value, basestring)) and (not hasattr(first_value, "lower")):
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

    @classmethod
    def ensure(cls, seq):
        """ if it's already SentencesAsWordLists, just return it. if not, wrap it (which triggers sanity_check())
        """
        if isinstance(seq, cls):
            return seq
        else:
            return cls(seq)

    def sanity_check(self):
        """
        >>> import pytest
        >>> assert SentencesAsWordLists([["oops", "you", "passed..."], ["a", "sentence", "list"]])
        >>> with pytest.raises(ValueError): SentencesAsWordLists(["oops", "it's", "a", "flat", "list", "of", "words"])
        >>> with pytest.raises(ValueError): WordList([["oops", "you", "passed..."], ["a", "sentence", "list"]])
        """
        if self.data:
            if isinstance(self.data[0], basestring) or hasattr(self.data[0], "lower"):
                raise ValueError("should be list of lists-of-strings, appears to be list of strings")

    def unwrap(self):
        """ return internal list (useful when we need to pass to something that is over-strict about type-checking)
        """
        try:
            # if self.data is a list of WordList instances, this will work
            return [word_list.unwrap() for word_list in self.data]
        except AttributeError:
            return [word_list for word_list in self.data]


# ===============================================================

# for when you just want a quick-and-dirty rejoiner
rejoin = JoinerWhitespace().join

# alias these since they are "NLTK recommended," and  outside of this module, caller shouldn't have to think about
# subtleties of NLTK recommending (Punkt combined with Treebank)
WordTokenizerNLTK = WordTokenizerTreebank
SentenceTokenizerNLTK = SentenceTokenizerPunkt

tokenizer_classes_by_nickname = {
    "nltk": SentenceTokenizerNLTK,
    "just_whitespace": SentenceTokenizerWhitespace,
    "markovify": SentenceTokenizerMarkovify
}

TOKENIZER_NICKNAMES = tokenizer_classes_by_nickname.keys()


def create_sentence_tokenizer(nickname):
    return tokenizer_classes_by_nickname[nickname]()


joiner_classes_by_nickname = {
    "just_whitespace": JoinerWhitespace,
    "moses": JoinerMoses,
    "random_indent": JoinerMosesWithRandomIndent,
    "random_enjamb": JoinerMosesWithRandomEnjambment,
}


def create_joiner(nickname):
    return joiner_classes_by_nickname[nickname]()
