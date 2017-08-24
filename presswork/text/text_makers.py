# -*- coding: utf-8 -*-
""" building blocks for making new sentences+words from generative models; composition is encouraged (pun intended)

-------------------------------------------------------------------------------
usage notes -- TextMaker & subclasses are the main entry point
===============================================================================

    * most common usage is just create_text_maker(<text>). that uses default class, and default settings.
        but caller can also get them by a nickname (CLI needs this), or for more custom, directly instantiate classes.
        (examples below put in tiny amount of input text so that output is same every time.)

        >>> from presswork.text.grammar import rejoin
        >>> text_maker = create_text_maker(input_text="Foo is better than bar")
        >>> result = text_maker.make_sentences(1)
        >>> assert rejoin(result).startswith("Foo")
        >>> text_maker = create_text_maker(input_text="Foo is better than bar", class_or_nickname="crude")
        >>> result = text_maker.make_sentences(1)
        >>> assert rejoin(result).startswith("Foo")
        >>> text_maker = TextMakerCrude()
        >>> assert text_maker.input_text("Foo is better than bar")
        >>> result = text_maker.make_sentences(1)
        >>> assert rejoin(result).startswith("Foo")

    * composition is encouraged for putting together further variants. this can be done on the fly;
        attributes such as TextMaker.strategy are *not* protected, so they can be accessed directly and customized.

    * today this module only works with models that parse into 'sentences' and 'words', in natural languages
        that read from left to right, with whitespace separation between words. it should be possible to
        go beyond just "English," but significant redesign would be needed for significantly differrent languages

-------------------------------------------------------------------------------
design notes -- TextMaker etc.
===============================================================================

    * favor composition.
        TextMaker subclasses should be basically adapters, adapting other implementations to this common interface.
        (so most methods *should* be forward methods to other strategies. should avoid having its own logic.)

    * as maintainer, I want to keep TextMaker interface restricted to essentials. this is to reduce scope,
            but also as an exercise to see what the common-denominator essential interface is.
            if I end up extending beyond just markov chains, could there still be a useful common interface,
            that takes in text, models it <somehow>, then outputs N sentences?
        * dumping models to text and persisting - are NOT supported at this level for now. by design.
            iff needed, the strategies can be accessed directly for their own persistence features.
        * keeping TextMaker interface minimal also encourages separating the concerns for the other pieces,
            which then supports more mix-and-match (experiment with different compositions of behaviors)

    * as *USER* I might find features are missing from TextMaker, but I these notes-to-self:
        * realize you can access 'strategy' attribute for customizations, or to overwrite with another instance.
        * consider using the third-party libraries directly. or if you repeatedly do same things then consider
            refactoring that into another strategy and/or subclass of this.

"""
import logging

from presswork import constants
from presswork.sanitize import SanitizedString
from presswork.text import _crude_markov
from presswork.text import grammar
from presswork.text import thirdparty

logger = logging.getLogger("presswork")



class TextMakerIsLockedException(ValueError):
    """ raise when someone tries to mutate TextMaker input text/state size/ etc after it is already loaded & locked
    """

class BaseTextMaker(object):
    """ common-denominator interface for making text from a generative model - so far, from markov chain models

    Subclasses should be "lazy" until input_text() is called. after that, it "locks" and it can only make_sentences().
    Typical usage should use the `create_text_maker` factory within this module, all 'convenience' is moved to there,
    so we can keep the class constructors minimal and DRY.

    Q:  Why lock after input_text is called?
    A:  Trying to keep things easy, but safe. With at least 1 impl (PyMarkovChain), calling input_text() more than once
        caues issues. additionally, changing ngram_size after calling input_text() could cause astonishment.
        Instead of allowing for some cases and denying for others, we just keep it consistent/safe.

    See also: overall design notes at the header of the module, which covers TextMakers as well as collaborators.
    """

    def __init__(self, ngram_size=constants.DEFAULT_NGRAM_SIZE, sentence_tokenizer=None):
        """
        :param ngram_size: state size AKA window size AKA N-gram size.
            this needs to be known both at the generate/load of the model (i.e. markov chain),
            and at the text generation time (and they need to match).

        :param sentence_tokenizer: one of the tokenizers from `grammar` module, or something that quacks like one.
            defaults to the 'cheap' option, all based on whitespace.
            what's expected: sentence_tokenizer.tokenize() => [ [word, word, ...], [word, word, ...], ... ].

        note: the word_tokenizer strategy is pluggable too, but it is something you attach to a sentence_tokenizer.
        i.e. sentence_tokenizer=SentenceTokenizer(word_tokenizer=WordTokenizer). more details in `grammar` module.
        """
        self._ngram_size = ngram_size

        if not sentence_tokenizer:
            logger.debug("no sentence_tokenizer argument given, defaulting to cheapest tokenizers")
            sentence_tokenizer = grammar.SentenceTokenizerWhitespace()
        self._sentence_tokenizer = sentence_tokenizer

        self._locked = False

    def make_sentences(self, count):
        return NotImplementedError()

    def input_text(self, input_text):
        """ build a fresh model from input text. (does not generate text - call make_sentences() to generate text.)

        * base class input_text() is public and handles pre/post hook that is same for all variants.
        * each subclass implements _input_tokenized(), private, implements the strategy. (may just adapt/forward)
        implements the *common* parts (not specific to subclasses)

        :return: returns the tokenized text (that was tokenzed with self._sentence_tokenizer). mainly this is
            useful for testing, debugging, etc. this is
        """
        if self.is_locked:
            raise TextMakerIsLockedException("locked! has input_text() already been called? (can only be called once)")

        input_text = SanitizedString(input_text)
        sentences_as_word_lists = self._sentence_tokenizer.tokenize(input_text)

        self._input_text(sentences_as_word_lists)
        self._lock()

        return sentences_as_word_lists

    def _input_text(self, sentences_as_word_lists):
        """ build a fresh model from this input text. (private; should contain the impl or adapter.)

        :param sentences_as_word_lists: list of lists. grammar.SentencesAsWordLists, or anything that quacks like that.
            typically passed in from self._sentence_tokenizer.tokenize()
        """
        raise NotImplementedError()

    @property
    def ngram_size(self):
        return self._ngram_size

    @ngram_size.setter
    def ngram_size(self, value):
        """ refuses to change ngram_size property if the TextMaker has been locked
        """
        if self.is_locked:
            raise TextMakerIsLockedException(
                    "locked! ngram_size cannot be changed after locking (such as after loading input text), "
                    "to avoid unintended mixing of ngram_size values")
        self._ngram_size = value

    def _lock(self):
        """ lock upon first input_text call, to avoid changing things after loading input text for the first time

        (this is private, subclasses or callers should not need to call it or think about it.)
        """
        self._locked = True

    @property
    def is_locked(self):
        return self._locked

    def clone(self):
        """ create a new instance with the same constructor arguments. (helps with a test case, if nothing else)
        """
        if self.is_locked:
            raise TextMakerIsLockedException('instance is locked! copying might be unsafe, aborting for max safety')
        return self.__class__(ngram_size=self.ngram_size, sentence_tokenizer=self._sentence_tokenizer)

    def __repr__(self):
        return "{}(ngram_size={!r}, sentence_tokenizer={!r})".format(
                self.__class__.__name__, self.ngram_size, self._sentence_tokenizer)



class TextMakerPyMarkovChain(BaseTextMaker):
    """ text maker with implementation by PyMarkovChain[WithNLTK], pretty well-behaved but no performance tuning

    For most usages, this is preferable to 'crude'; but 'markovify' is the most preferable.
    """
    NICKNAME = 'pymc'

    def __init__(self, *args, **kwargs):
        super(TextMakerPyMarkovChain, self).__init__(*args, **kwargs)
        self.strategy = thirdparty._pymarkovchain.PyMarkovChainForked(
            window=self.ngram_size,
            sentence_tokenizer=self._sentence_tokenizer,
            # avoid surprising side effects: force clean slate. (see module docstring for rationale.)
            db_file_path=None,
        )

    def _input_text(self, sentences_as_word_lists):
        self.strategy.database_init(sentences_as_word_lists)

    def make_sentences(self, count):
        result = self.strategy.make_sentences_list(number=count)
        return grammar.SentencesAsWordLists(result)


class TextMakerCrude(BaseTextMaker):
    """ text maker using 'crude' implementation, which is homegrown and indeed, crude.

    For most usages, the other strategies should be preferred. (rationale for keeping is explained in _crude_markov,
    module docstring, etc. - but in short, it has to do with how this is just a repository for playing around.)
    """
    NICKNAME = 'crude'

    def __init__(self, *args, **kwargs):
        super(TextMakerCrude, self).__init__(*args, **kwargs)
        # In the case of _crude_markov it's implemented with just functions on a module (not a class)
        self.strategy = _crude_markov
        self._model = {}

    def _input_text(self, sentences_as_word_lists):
        self._model = self.strategy.crude_markov_chain(sentences_as_word_lists, ngram_size=self.ngram_size)

    def make_sentences(self, count):
        iter_sentences_of_words = self.strategy.iter_make_sentences(
                crude_markov_model=self._model, ngram_size=self.ngram_size, count=count)
        return grammar.SentencesAsWordLists(iter_sentences_of_words)


# ====================================================================================================

_classes_by_nickname = {klass.NICKNAME: klass for klass in BaseTextMaker.__subclasses__()}
CLASS_NICKNAMES = _classes_by_nickname.keys()
DEFAULT_TEXT_MAKER_NICKNAME = "crude" # TODO change the default to markovify


def _get_text_maker_class(name_or_nickname):
    """ helper for the factory below, and test suite.
    """

    classes_by_name = {klass.__name__: klass for klass in BaseTextMaker.__subclasses__()}
    klass = classes_by_name.get(name_or_nickname, _classes_by_nickname.get(name_or_nickname, None))

    if klass is None:
        raise KeyError("could not find text maker class for {!r}".format(name_or_nickname))

    return klass


def create_text_maker(
        class_or_nickname=DEFAULT_TEXT_MAKER_NICKNAME,
        sentence_tokenizer_nickname_or_instance=None,
        input_text=None,
        ngram_size=constants.DEFAULT_NGRAM_SIZE,):
    """ convenience factory to just "gimme a text maker" without knowing exact module layout. nicknames supported.

    rationale: I *do* want an easy way for callers to make these, but I want to keep the classes minimal -
    little to no special logic in the constructors.

    :param input_text: the input text to load into the TextMaker class. (if not given, you can load it later.)
    :param class_or_nickname: (optional) specific nickname of class to use e.g. 'crude', 'pymc' 'markovify'
        can also just pass in an exact class. if not given, will use the default.
    :param sentence_tokenizer_nickname_or_instance: i.e. 'nltk', 'whitespace', or specific customized instance.
        if not given, does not override; TextMaker class decides.
    """

    if isinstance(class_or_nickname, basestring):
        ATextMakerClass = _get_text_maker_class(name_or_nickname=class_or_nickname)
    else:
        if callable(class_or_nickname):
            ATextMakerClass = class_or_nickname
        else:
            raise ValueError('{!r} is not callable. please pass a valid class or nickname'.format(class_or_nickname))

    if isinstance(sentence_tokenizer_nickname_or_instance, basestring):
        sentence_tokenizer_nickname = sentence_tokenizer_nickname_or_instance
        ASentenceTokenizerClass = grammar.tokenizer_classes_by_nickname[sentence_tokenizer_nickname]
        sentence_tokenizer = ASentenceTokenizerClass()
    else:
        sentence_tokenizer = sentence_tokenizer_nickname_or_instance

    text_maker = ATextMakerClass(ngram_size=ngram_size, sentence_tokenizer=sentence_tokenizer)

    if input_text:
        # SanitizedString 'memoizes' to avoid redundant sanitization - so it's no problem to call redundantly
        input_text = SanitizedString(input_text)
        text_maker.input_text(input_text)

    return text_maker
