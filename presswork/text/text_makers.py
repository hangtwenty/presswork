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


# TODO(hangtwenty) replace with classes, yes this basic type, but also NLTK kinds
def rejoin(sentences_of_words, sentence_sep="\n", word_sep=" "):
    return sentence_sep.join(word_sep.join(word for word in sentence) for sentence in sentences_of_words)



class BaseTextMaker(object):
    """ common-denominator interface for making text from a generative model - so far, from markov chain models

    SEE ALSO: design notes at the header of the module.
    """

    DEFAULT_STATE_SIZE = constants.DEFAULT_NGRAM_SIZE

    # TODO rename state_size to ngram_size; that is more 'high level' than being specific to markov's lower level detail of dealing with n 'states'...
    def __init__(self, state_size=DEFAULT_STATE_SIZE):
        """
        :param state_size: state size AKA window size AKA N-gram size. how many tokens (e.g. words) per 'prefix'; or,
            the 'N' in 'N-gram'. one more way to think of it: how long of 'prefixes' to model in the text.
            increasing this will increase the 'tightness' (and 'familiarity' or 'closeness'). 2 is a good default.
            this DOES get passed right to the underlying markov chain model, but we DO need to know it at the top
            level too, for generation. if we don't, we'd have to make some inferences (unnecessary complexity...)
        """
        self.state_size = state_size


    def __repr__(self):
        # TODO ensure all params are in this repr()
        return "{}(state_size={})".format(self.__class__.__name__, self.state_size)

    def input_text(self, string):
        """ build a fresh model from this input text.

        specfically take a string of input text, parse into SentencesAndWords, and load into the strategy instance.
        """
        raise NotImplementedError()

    def make_sentences(self, count):
        return NotImplementedError()


class TextMakerPyMarkovChain(BaseTextMaker):
    """ text maker with implementation by PyMarkovChain[WithNLTK], pretty correct but no performance tuning
    """
    NICKNAME = 'pymc'

    def __init__(self, *args, **kwargs):
        super(TextMakerPyMarkovChain, self).__init__()
        self.strategy = _pymarkovchain_fork.PyMarkovChainWithNLTK(
                # avoid surprising side effects: force clean slate. (see module docstring for rationale.)
                db_file_path=None,
                window=self.state_size)
        assert isinstance(self.strategy, _pymarkovchain_fork.PyMarkovChainWithNLTK), "PyCharm type hint"

    def input_text(self, string):
        # TODO(hangtwenty) instead of letting this impl do its own sentence handling,
        # should instead be doing SentencesAndWords thing, and passing THAT...
        # FIXME this MIGHT end up meaning that I delete _pymarkovchain_fork from this repo..........
        # and can just use it as a direct dependency....!? Need to look at that source.
        self.strategy.database_init(unicode(string))

    def make_sentences(self, count):
        return self.strategy.make_sentences_list(number=count)


class TextMakerCrude(BaseTextMaker):
    """ text maker using homegrown/minimal/basic implementation, not very correct and poor performance

    this one shouldn't be used often, should be used for development and exploration during development or play.
    """
    NICKNAME = 'crude'

    def __init__(self, *args, **kwargs):
        super(TextMakerCrude, self).__init__()
        # In the case of _crude_markov it's implemented with just functions on a module
        self.strategy = _crude_markov
        self._model = {}

    def input_text(self, string):
        self._model = self.strategy.crude_markov_chain(source_text=string, ngram_size=self.state_size)

    def make_sentences(self, count):
        iter_sentences_of_words = self.strategy.iter_make_sentences(
                crude_markov_model=self._model, ngram_size=self.state_size, count_of_sentences_to_generate=count)
        return list(iter_sentences_of_words)


# ====================================================================================================

DefaultTextMaker = TextMakerCrude  # TODO(hangtwenty) change default to markovify later on.

# Table of class lookups by stringified names & nicknames - used by different contexts mostly in other modules.
classes_by_name = {klass.__name__: klass for klass in BaseTextMaker.__subclasses__()}

classes_by_nickname = {klass.NICKNAME: klass for klass in BaseTextMaker.__subclasses__()}
classes_by_nickname["default"] = DefaultTextMaker

classes_by_all_names = {}
classes_by_all_names.update(classes_by_name)
classes_by_all_names.update(classes_by_nickname)

# TODO(hangtwenty) should expose state_size etc here
def create_text_maker(
        input_text=None,
        class_or_nickname="default",
        state_size=constants.DEFAULT_NGRAM_SIZE,):
    """ convenience factory to just "gimme a text maker" without knowing exact module layout. nicknames supported.

    :param input_text: the input text to load into the TextMaker class. (if not given, you can load it later.)
    :param class_or_nickname: (optional) specific nickname of class to use e.g. 'crude', 'pymc' 'markovify'
        can also just pass in an exact class. if not given, will use the default.
    """

    # SanitizedString avoids redundant sanitization, so it is OK to call redundantly in the module
    input_text = SanitizedString(input_text)

    try:
        # try looking it up as if it is a nickname
        klass = classes_by_all_names[class_or_nickname]
    except KeyError:
        # ah, assume it is the class itself
        klass = class_or_nickname

    if not callable(klass):
        raise ValueError('klass={!r} is not callable. please pass a valid class or nickname'.format(klass))

    text_maker = klass(state_size=state_size)

    if input_text:
        text_maker.input_text(input_text)

    return text_maker
