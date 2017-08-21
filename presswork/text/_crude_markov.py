""" Very basic homegrown implementation for fun & reference purposes.

The implementations in `thirdparty` are preferable for actual usage, outside of development and play purposes.
Notable deficiencies of the 'crude' implementation:
    - no maturity or battle testing, so haven't found the edge cases yet
    - no optimization of memory usage: instead of storing #s of probabilities, raw lists are used
        (Simplest Thing That Could Possibly Work, demos the essential algorithm, that's all)
    - no optimization of lookups for performance boosts (contrast with jsvine/markovify)

Why it's here:
    - provides something to contrast the other implementations with, for testing and benchmarking
    - provides a stripped-down reference implementation for understanding the algorithm (which is fundamentally similar
    to the other implementations). Note, it's not a minimal 'pure' Markov Chain impl., rather it's a minimal
    'Markov Chain Text Generator' impl. It is defiinitely narrowed to the domain.
    - this whole repository is just for fun, this file included
"""

# TODO doctests where it makes sense. (don't forget to add --doctest-modules to tox.ini etc)

import logging
import pprint
import random

logger = logging.getLogger("presswork")

EXAMPLE_SOURCE = u"""
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
"""

# By using empty string as start-of-sentence-marker, we can avoid special handling later.
START_SYMBOL = u""
END_SYMBOL = u""

DEFAULT_NGRAM_SIZE = 2


def _crude_split_sentences(string_of_full_text):
    # ATTN: this function is especially crude. it is only left here as a default/fallback.
    # Idea is that, in the calling module (text_makers), you can wire in a better splitter. # TODO make it so
    return tuple(string_of_full_text.splitlines())


def _crude_split_words(string_of_sentence):
    # ATTN: this function is especially crude. it is only left here as a default/fallback.
    # Idea is that, in the calling module (text_makers), you can wire in a better splitter. # TODO make it so
    return tuple(string_of_sentence.split())


def crude_markov_chain(
        source_text=EXAMPLE_SOURCE,
        ngram_size=DEFAULT_NGRAM_SIZE,
        fn_to_split_sentences=_crude_split_sentences,
        fn_to_split_words=_crude_split_words,
):
    # FIXME: this should just take list-of-lists (sentences, words) ; caller should do splitting etc.
    # def iter_make_sentences(source_text) :
    #       source_text -> sentences_and_words = [[word, ...], [word, ...]] (using composable fns for splitting);
    #       model = chain(sentences_and_words)
    #       <exercise the model>
    # def iter_make_sentences(model) :
    #       <exercise the model>
    # so yeah pretty easy to see how refactoring to a TextMaker class would help.

    # model = {
    #     # TODO mmm can I get rid of the starter
    #     (START_SYMBOL * ngram_size): [],
    # }

    model = {}

    # TODO really no source text handling should be done here, so move it out... this should take [[word,...]] already processed
    if not source_text:
        return model

    for sentence in _crude_split_sentences(source_text):
        words = fn_to_split_words(sentence)

        words_with_padding = ngram_for_sentence_start(ngram_size) + words + (END_SYMBOL,)

        for i in xrange(0, len(words) + 1):
            ngram = tuple(words_with_padding[i:(i + ngram_size)])

            try:
                next_word = words_with_padding[i + ngram_size]
            except IndexError:
                # TODO(hangtwenty) now that I have the padding (END_SYMBOL,) should I get rid of the IndexError catch?
                # .................. or, get rid of the padding (END_SYMBOL,) and keep this catch?
                next_word = END_SYMBOL

            # Re: memory usage --
            # In this 'crude' model, we store lists of literal occurrences.
            # If we were optimizing for memory usage, we could 'reduce' to Counter.
            #       model[ngram][<unique_next_word>] = Counter
            # Other implementations (rightly) do exactly that. (Or normalize the Counter to 0.0-1.0 probability).
            # Here, we will continue to optimize for obviousness, at the expense of memory usage.
            if model.get(ngram, None) is None:
                model[ngram] = [next_word]
            else:
                model[ngram].append(next_word)

    if logger.level == logging.DEBUG:
        logger.debug(u'model=\n{}'.format(pprint.pformat(model, width=2)))

    return model


def is_empty_model(model):
    if not model:
        return True

    if len(model.keys()) == 1:
        # i.e. {('', ..): ['', ..]} (when input is empty string we get this model, and it is best to short-circuit)
        return True

    return False


def iter_make_sentences(
        crude_markov_model,
        ngram_size=DEFAULT_NGRAM_SIZE,
        count_of_sentences_to_generate=100,
        max_loops_per_sentence=25):

    current_ngram = None
    sentence = []
    end_sentence = False

    _sentences_counter = 0
    _per_sentence_loop_counter = 0

    if is_empty_model(crude_markov_model):
        yield sentence
        raise StopIteration()

    while _sentences_counter < count_of_sentences_to_generate:
        logger.debug('current sentence = {}, i (sentence#) = {}, per_sentence_loop_counter={}'.format(
                sentence, _sentences_counter, _per_sentence_loop_counter))

        if not current_ngram:
            current_ngram = ngram_for_sentence_start(ngram_size)

        try:
            next_word_options = crude_markov_model[current_ngram]
            next_word = random.choice(next_word_options)
            sentence.append(next_word)
            # logger.debug('this sentence now = {}'.format(sentence))
            current_ngram = current_ngram[1:] + (next_word,)
        except (KeyError, IndexError):
            # when we hit a 'dead end' we consider that the end of the 'sentence'
            end_sentence = True

        if _per_sentence_loop_counter >= max_loops_per_sentence:
            # also a fallback if sentence is going on too long (infinite loops are possible otherwise)
            end_sentence = True

        if end_sentence:
            _sentences_counter += 1
            _per_sentence_loop_counter = 0
            current_ngram = None
            end_sentence = False

            yield sentence
            sentence = []
        else:
            _per_sentence_loop_counter += 1

    raise StopIteration()


def ngram_for_sentence_start(ngram_size):
    """ makes more believable sentences if (a) model has special sentence-start and (b) gen uses same sentence starts

    see the usage, and it'll make more sense ;-) refactored up to a function only to keep it DRY/ avoid future mistakes
    """
    return tuple((START_SYMBOL,) * ngram_size)
