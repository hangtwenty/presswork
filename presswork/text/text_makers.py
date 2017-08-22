# -*- coding: utf-8 -*-
""" building blocks for making new sentences+words from generative models; composition is encouraged (pun intended)

-------------------------------------------------------------------------------
usage notes -- TextMaker & subclasses are the main entry point
===============================================================================

    * most common usage is just create_text_maker(<text>). that uses default class, and default settings.
        but caller can also get them by a nickname (CLI needs this), or for more custom, directly instantiate classes.
        (examples below put in tiny amount of input text so that output is same every time.)

        >>> text_maker = create_text_maker("Foo is better than bar")
        >>> result = text_maker.make_sentences(1)
        >>> assert rejoin(result).startswith("Foo")
        >>> text_maker = create_text_maker("Foo is better than bar", class_or_nickname="crude")
        >>> result = text_maker.make_sentences(1)
        >>> assert rejoin(result).startswith("Foo")
        >>> text_maker = TextMakerCrude()
        >>> text_maker.input_text("Foo is better than bar")
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
from presswork.text import _crude_markov
from presswork.text import _pymarkovchain_fork

from presswork.sanitize import SanitizedString

logger = logging.getLogger("presswork")


# TODO(hangtwenty) rejoiner aka composer classes... but still keep a convenience-function that's just like "rejoin it the default way" yet
def rejoin(sentences_of_words, sentence_sep="\n", word_sep=" "):
    return sentence_sep.join(word_sep.join(word for word in sentence) for sentence in sentences_of_words)


class TextMakerIsLockedException(ValueError):
    """ raise when someone tries to mutate TextMaker input text/state size/ etc after it is already loaded & locked
    """

class BaseTextMaker(object):
    """ common-denominator interface for making text from a generative model - so far, from markov chain models

    Subclasses can be "lazy" until input_text() is called. after that, it "locks" and only text generation is possible.
    Typical usage should use the `create_text_maker` factory within this module, all 'convenience' is moved to there,
    so we can keep these minimum-necessary.

    Q:  Why lock after input_text is called?
    A:  trying to keep things easy, but safe. With 1+ backends, calling input_text() repeatedly may not
        achieve desired results. additionally, changing state_size after calling input_text() could cause astonishment.
        Instead of allowing for some and denying for others, we just keep it consistent.

    See also: overall design notes at the header of the module, which covers TextMakers as well as collaborators.
    (Won't re-hash those notes here.)
    """

    DEFAULT_STATE_SIZE = constants.DEFAULT_NGRAM_SIZE

    # TODO rename state_size to ngram_size; that is more 'high level' than being specific to markov's lower level detail of dealing with n 'states'...
    def __init__(self, state_size=DEFAULT_STATE_SIZE):
        """
        :param state_size: state size AKA window size AKA N-gram size. how many tokens (e.g. words) per 'prefix'; or,
            the 'N' in 'N-gram'. this needs to be known both at the generate/load of the model (i.e. markov chain),
            and at the text generation time (and they need to match).
        """
        self._state_size = state_size
        self._locked = False

    def clone(self, ):
        if self.is_locked:
            raise TextMakerIsLockedException('instance is locked! copying might be ago, aborting for max safety')

        # TODO(hangtwenty) ensure this does all relevant params from constructor
        return self.__class__(state_size=self.state_size)

    def _lock(self):
        """ lock upon first input_text call, to avoid changing things after loading input text for the first time

        (this is private, subclasses or callers should not need to call it or think about it.)
        """
        self._locked = True

    @property
    def is_locked(self):
        return self._locked

    @property
    def state_size(self):
        return self._state_size

    @state_size.setter
    def state_size(self, value):
        """ refuses to change state_size property if the TextMaker has been locked
        """
        if self.is_locked:
            raise TextMakerIsLockedException(
                    "locked! state_size cannot be changed after locking (such as after loading input text), "
                    "to avoid unintended mixing of state_size values")
        self._state_size = value

    def __repr__(self):
        # TODO ensure all params are in this repr()
        return "{}(state_size={})".format(self.__class__.__name__, self.state_size)

    def _input_text(self, string):
        """ build a fresh model from this input text. PRIVATE but has real implementation. see also `input_text()
        """
        raise NotImplementedError()

    def input_text(self, string):
        """ build a fresh model from this input text. PUBLIC - handles _lock to ensure input only happens once
        """
        if self.is_locked:
            raise TextMakerIsLockedException("locked! has input_text() already been called? (can only be called once)")
        result = self._input_text(string)
        self._lock()
        return result

    def make_sentences(self, count):
        return NotImplementedError()


class TextMakerPyMarkovChain(BaseTextMaker):
    """ text maker with implementation by PyMarkovChain[WithNLTK], pretty well-behaved but no performance tuning

    For most usages, this is preferable to 'crude' at least. but it is not the best choice overall. (see 'markovify')
    """
    NICKNAME = 'pymc'

    def __init__(self, *args, **kwargs):
        super(TextMakerPyMarkovChain, self).__init__()
        self.strategy = _pymarkovchain_fork.PyMarkovChainWithNLTK(
                # avoid surprising side effects: force clean slate. (see module docstring for rationale.)
                db_file_path=None,
                window=self.state_size)
        assert isinstance(self.strategy, _pymarkovchain_fork.PyMarkovChainWithNLTK), "PyCharm type hint"

    def _input_text(self, string):
        self.strategy.database_init(unicode(string))

    def make_sentences(self, count):
        return self.strategy.make_sentences_list(number=count)


class TextMakerCrude(BaseTextMaker):
    """ text maker using 'crude' implementation, which is homegrown and indeed, crude.

    For most usages, the other strategies should be preferred. (rationale for keeping is explained in _crude_markov,
    module docstring, etc. - but in short, it has to do with how this is just a repository for playing around.)
    """
    NICKNAME = 'crude'

    def __init__(self, *args, **kwargs):
        super(TextMakerCrude, self).__init__()
        # In the case of _crude_markov it's implemented with just functions on a module
        self.strategy = _crude_markov
        self._model = {}

    def _input_text(self, string):
        self._model = self.strategy.crude_markov_chain(source_text=string, ngram_size=self.state_size)

    def make_sentences(self, count):
        iter_sentences_of_words = self.strategy.iter_make_sentences(
                crude_markov_model=self._model, ngram_size=self.state_size, count_of_sentences_to_generate=count)
        return list(iter_sentences_of_words)


# ====================================================================================================

DefaultTextMaker = TextMakerCrude  # TODO(hangtwenty) change default to markovify later on.

_classes_by_nickname = {klass.NICKNAME: klass for klass in BaseTextMaker.__subclasses__()}
CLASS_NICKNAMES = _classes_by_nickname.keys()


def _get_text_maker_class(string):
    """ helper for the factory below, and test suite, to help this module take care of/ expose itself
    """
    if string == "default":
        return DefaultTextMaker

    classes_by_name = {klass.__name__: klass for klass in BaseTextMaker.__subclasses__()}
    klass = classes_by_name.get(string, _classes_by_nickname.get(string, None))

    if klass is None:
        raise KeyError("could not find text maker class for {!r}".format(string))

    return klass


def create_text_maker(
        input_text=None,  # TODO also support passing in splitter functions & joiner functions
        class_or_nickname="default",
        state_size=constants.DEFAULT_NGRAM_SIZE,):
    """ convenience factory to just "gimme a text maker" without knowing exact module layout. nicknames supported.

    rationale: I *do* want an easy way for callers to make these, but I want to keep the classes minimal -
    little to no special logic in the constructors.

    :param input_text: the input text to load into the TextMaker class. (if not given, you can load it later.)
    :param class_or_nickname: (optional) specific nickname of class to use e.g. 'crude', 'pymc' 'markovify'
        can also just pass in an exact class. if not given, will use the default.
    """

    if isinstance(class_or_nickname, basestring):
        klass = _get_text_maker_class(string=class_or_nickname)
    else:
        if callable(class_or_nickname):
            klass = class_or_nickname
        else:
            raise ValueError('{!r} is not callable. please pass a valid class or nickname'.format(class_or_nickname))

    # TODO(hangwenty) expose other arguments maybe
    text_maker = klass(state_size=state_size)

    if input_text:
        # SanitizedString 'memoizes' to avoid redundant sanitization - so it no problem to call redundantly
        input_text = SanitizedString(input_text)
        text_maker.input_text(input_text)

    return text_maker
