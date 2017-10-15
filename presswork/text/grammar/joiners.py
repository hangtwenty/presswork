""" Joiners - some straightforward, some quirky. From tokenized sentences and words, to text

-------------------------------------------------------------------------------
design notes -- Joiners
===============================================================================

    * a Joiner takes in SentencesAsWordLists and joins the tokens back into strings. Various strategies.
    * so it is the same responsibility as a 'de-tokenizer' as NLTK calls it. but calling it a Joiner to keep it broad.
        * fair game: random or probabilistic whitespace variations (indentation, enjambment)

"""
import random

from nltk.tokenize.moses import MosesDetokenizer

from presswork.text.grammar.containers import SentencesAsWordLists


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

    def _join_sentences(self, sentences):
        """  takes SentencesAsWordLists and "re-joins" or "de-tokenizes" into a string.

            >>> joiner = Joiner(separate_sentences=" // ")
            >>> assert joiner._join_sentences([[]]) == ""
            >>> assert joiner._join_sentences(None) == ""
            >>> print joiner._join_sentences([['this', 'is', 'the'], ['expected', 'data', 'structure']])
            this is the // expected data structure

        :param sentences: Should typically be a SentencesAsWordLists instance; but it's duck-typed. Builtins welcome
        :type sentences_as_word_lists: SentencesAsWordLists
        :rtype: basestring
        """
        if sentences:
            if len(sentences) > 1:
                result = self._join_word_seq(sentences[0]) + u"".join(
                        (self.between_sentences() or u"") + self._join_word_seq(sentence)
                        for sentence in sentences[1:]
                )
            else:
                result = self._join_word_seq(sentences[0])
        else:
            result = u""

        return result.strip()

    def _join_word_seq(self, word_list):
        # calls between_sentences() in between each - while this is extra calls for some joiner strategies,
        # overall it keeps things maximally flexible: between_sentences() can be overridden to return dynamic values
        word_list = filter(None, word_list)
        if word_list:
            if len(word_list) > 1:
                return word_list[0] + u"".join((self.between_words() or u"") + word for word in word_list[1:])
            else:
                return word_list[0]
        else:
            return u""

    def between_words(self):
        """ default is - just return self._word_separator. However, quirky weird Joiners can override.
        """
        return self._word_separator

    def between_sentences(self):
        """ default is - just return self._sentence_separator. However, quirky weird Joiners can override.
        """
        return self._sentence_separator

    def __repr__(self):
        return "{}(separate_sentences={!r}, separate_words={!r})".format(
                self.__class__.__name__, self._sentence_separator, self._word_separator)


class JoinerWhitespace(Joiner):
    """ Just hardcodes to newlines and spaces (regardless of whether the base class is using the same defaults)

        >>> print JoinerWhitespace().join([['foo', 'bar', 'baz'], ['quux']])
        foo bar baz
        quux
    """

    def __init__(self, separate_sentences="\n", separate_words=" "):
        super(JoinerWhitespace, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words)


class JoinerNLTK(Joiner):
    """ Wraps NLTK's Moses De-tokenizer. This is NLTK's recommended de-tokenizer at time of wirting.

    NOTE: Whenever using any NLTK detokenizer, it is best to put back through *this* strategy (not 'just_whitespace'),
    as those tokenizers separate punctuation out ... That separation is good for markov-model-training,
    but bad for display if left alone ("Lots of this . Extra paces ."). MosesDetokenizer handles it well.

    http://www.nltk.org/api/nltk.tokenize.html

    >>> joiner = JoinerNLTK(separate_sentences=" ")
    >>> print joiner.join([['Foo', 'bar', 'baz', '.'], ['More', 'of', 'the', 'same.']])
    Foo bar baz. More of the same.
    >>> print joiner.join([['How', 'do', 'you', 'do', '?'], ['Fine,', 'you', '?']])
    How do you do? Fine, you?
    >>> assert joiner.join([[]]) == ""
    >>> assert joiner.join([[""]]) == ""
    >>> print JoinerNLTK().join([["Do ", " not ", "  leave ", "extra", "spaces  ", ".", " Around", "punct .  " ]])
    Do not leave extra spaces. Around punct.
    >>> print JoinerNLTK().join([['text . . . is fun : very , very fun !! ! yada: yada blah ; hi']])
    text... is fun: very, very fun!!! yada: yada blah; hi
    >>> already_good = 'Unless you are a linguist who has studied garden path sentences, the answer is probably "no".'
    >>> assert JoinerNLTK().join([already_good.split()]) == already_good

    """

    def __init__(self,
                 separate_sentences=" ",  # moses can be suitable for prose if we don't insert newlines
                 separate_words=" "):
        super(JoinerNLTK, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words)

        self.detokenizer = MosesDetokenizer(lang="en")

    def _join_word_seq(self, word_list):
        # passing to moses detokenizer is simple ...
        sentence_string = self.detokenizer.detokenize(word_list, return_str=True)

        # ... but in our terms, MosesDetokenizer assumes separate_words=" ". That's OK in some case,
        # but we want it so other separators can be passed in; AND so that the between_words() hook is still respected.
        # ... but to also respect custom word separator hook, we re-split & send to self._join_word_list
        sentence_string = super(JoinerNLTK, self)._join_word_seq(word_list=sentence_string.split())

        return sentence_string


class JoinerNLTKWithRandomIndent(JoinerNLTK):
    """ want crude pseudopoetry? just add pseudorandom indentation! Default is (0-8)*2spaces.

        >>> joiner = JoinerNLTKWithRandomIndent(_random=random.Random(456))
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
        >>> print joiner.join([["We", "should", ","], ["still", ",", "not", "have", "space", "around", "punct", "."]])
        We should,
                      still, not have space around punct.
        >>> assert joiner.join([[]]) == ""
        >>> assert joiner.join([[""]]) == ""
    """

    def __init__(self, separate_sentences="\n", separate_words=" ", _random=None):
        """
        :param _random: can pass in random.Random(...) (i.e. random with seed)
        """
        super(JoinerNLTKWithRandomIndent, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words)
        if _random:
            self.random = _random
        else:
            self.random = random.Random()

        self.indent_unit = (separate_words or u"") * 2

    def _random_indent(self):
        """ newline + 0-8 * (2 spaces). i.e. default: {0, 2 ... 16} spaces
        """
        separator = (self.indent_unit) * self.random.randint(0, 8)
        return separator

    def between_sentences(self):
        return self._sentence_separator + self._random_indent()


class JoinerNLTKWithRandomEnjambment(JoinerNLTKWithRandomIndent):
    """ want funkier pseudopoetry? don't just indent, enjamb! in addition to indenting, breaks sentences

        >>> joiner = JoinerNLTKWithRandomEnjambment(_random=random.Random(52))
        >>> # note, the <BLANKLINE> below is a doctest thing, in real output it would be real blank line
        >>> print joiner.join([["Expect", "some", "intense"], ["Indents", "and", "enjamb-", "ments"]])
        Expect some
        <BLANKLINE>
                intense
                        Indents and enjamb-
        <BLANKLINE>
              ments
        >>> joiner = JoinerNLTKWithRandomEnjambment(_random=random.Random(3))
        >>> print joiner.join([["Random", "runs"], ["How", "fun,", "how", "fun", "&", "done"]])
        Random runs
                How fun, how fun
                      & done
        >>> joiner = JoinerNLTKWithRandomEnjambment(_random=random.Random(5))
        >>> print joiner.join([["We", "should", ","], ["still", ",", "not", "have", "space", "around", "punct", "."]])
        We should,
                    still, not have space around
                        punct.
        >>> assert joiner.join([[]]) == ""
        >>> assert joiner.join([[""]]) == ""
    """

    def __init__(self, separate_sentences="\n", separate_words=" ", _random=None):
        super(JoinerNLTKWithRandomEnjambment, self).__init__(
                separate_sentences=separate_sentences, separate_words=separate_words, _random=_random)

        self.enjambment_chance = 0.2
        self.enjambment_extra_line_break_choices = [1, 1, 2]

    def between_words(self):
        """ achieves 'enjambment' by breaking sentences - inserting newlines & indents between 'words' too
        :return:
        """
        extra_whitespace = u""
        if self.random.random() < self.enjambment_chance:
            maybe_newline = self._sentence_separator * self.random.choice(self.enjambment_extra_line_break_choices)
            extra_whitespace = maybe_newline + self._random_indent().lstrip(self._sentence_separator)

        if extra_whitespace:
            return extra_whitespace
        else:
            return self._word_separator


# ===============================================================


joiner_classes_by_nickname = {
    "just_whitespace": JoinerWhitespace,
    "nltk": JoinerNLTK,
    "random_indent": JoinerNLTKWithRandomIndent,
    "random_enjamb": JoinerNLTKWithRandomEnjambment,
}

JOINER_NICKNAMES = joiner_classes_by_nickname.keys()


def create_joiner(nickname):
    return joiner_classes_by_nickname[nickname]()
