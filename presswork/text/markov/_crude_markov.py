# -*- coding: utf-8 -*-
""" Very basic homegrown implementation for fun & reference purposes.

If you're looking to generate text, don't *start* here. Start with the `text_makers` module!

    >>> model = crude_markov_chain([["A", "tokenized", "sentence."], ["A", "tokenized", "sentence."]])
    >>> for word_sequence in iter_make_sentences(model, count=2):
    ...     print " ".join([word.strip() for word in word_sequence if word.strip()])
    A tokenized sentence.
    A tokenized sentence.

The implementations in `thirdparty` are preferable for most use cases. Disadvantages to this implementation:
    * brand new & not as much battle-testing. fixed various edge cases, & things seem stable, but there could be more.
    * no optimization of memory usage: instead of storing #s of probabilities, raw lists are used
        (Simplest Thing That Could Possibly Work, demos the essential algorithm, that's all)
    * no optimization of lookups for performance boosts (contrast with jsvine/markovify)

Why it's kept around:
    * provides something to contrast the other implementations with, for testing and benchmarking
    * provides a stripped-down reference implementation for understanding the algorithm (which is fundamentally similar
    to the other implementations). Note, it's not a minimal 'pure' Markov Chain impl., rather it's a minimal
    'Markov Chain Text Generator' impl. It is defiinitely narrowed to the domain.
    * this whole repository is just for fun, this file included :)

"""
import logging
import pprint
import random

from presswork import constants

logger = logging.getLogger("presswork")

# By using empty string as start-of-sentence-marker, we can avoid special handling for this token later.
START_SYMBOL = u""
END_SYMBOL = u""


def crude_markov_chain(sentences_as_word_lists, ngram_size=constants.DEFAULT_NGRAM_SIZE, ):
    """ Build a Markov Chain model of sentences, words. Bare-essentials/crude implementation

    :param sentences_as_word_lists: list of lists of words/tokens. i.e. expects already-tokenized text.
        like [ [word, word, ...], [word, word, ...], ... ]
    :param ngram_size: the N in N-gram, AKA state size or window size. same as in general markov chains.
        2 or 3 are commonly used for text generation. higher than that can
    :return: a dict: { n-gram : [ possibility, possibility ...], ... }. Feed this to iter_make_sentences
        can be serialized to JSON, if you want to save a model for re-use.
    """
    model = {}

    if not sentences_as_word_lists:
        return model

    for word_sequence in sentences_as_word_lists:

        words_with_padding = ngram_for_sentence_start(ngram_size) + tuple(word_sequence) + (END_SYMBOL,)

        for i in xrange(0, len(word_sequence) + 1):
            ngram = tuple(words_with_padding[i:(i + ngram_size)])

            try:
                next_word = words_with_padding[i + ngram_size]
            except IndexError:
                next_word = END_SYMBOL

            if model.get(ngram, None) is None:
                model[ngram] = [next_word]
            else:
                # Re: memory usage -- see note in module docstring. (left unoptimized)
                model[ngram].append(next_word)

    if logger.level == logging.DEBUG:
        try:
            logger.debug(u'model=\n{}'.format(pprint.pformat(model, width=2)))
        except:
            logger.exception(u'hit exception while attempting to dump the model to debug-log. swallowing')

    return model


def iter_make_sentences(
        crude_markov_model, ngram_size=constants.DEFAULT_NGRAM_SIZE, count=100, max_loops_per_sentence=25):
    """ The fun part! Generate probable sentences based on a model. Bare-essentials/crude implementation.

    :param crude_markov_model: a model i.e. from crude_markov_chain() function
    :param ngram_size: N in N-gram, AKA state size or window size. same as elsewhere. must match ngram size of model.
    :return: (generator) yields lists-of-words.
    """
    if is_empty_model(crude_markov_model):
        logger.debug(u'is_empty_model({!r}) => True, short-circuit & return empty sentence'.format(crude_markov_model))
        yield []
        raise StopIteration()

    _model_ngram_size = len(crude_markov_model.keys()[0])
    if _model_ngram_size != ngram_size:
        logger.error(u"make_sentences ngram_size={}, but model ngram_size={!r}".format(ngram_size, _model_ngram_size))
        raise ValueError(u"ngram_size must match ngram_size of model.")

    current_ngram = None
    sentence = []
    end_sentence = False

    _sentences_counter = 0
    _per_sentence_loop_counter = 0

    while _sentences_counter < count:
        logger.debug(u'current sentence = {}, i (sentence#) = {}, per_sentence_loop_counter={}'.format(
                sentence, _sentences_counter, _per_sentence_loop_counter))

        if not current_ngram:
            current_ngram = ngram_for_sentence_start(ngram_size)

        try:
            next_word_options = crude_markov_model[current_ngram]
            next_word = random.choice(next_word_options)
            sentence.append(next_word)
            current_ngram = current_ngram[1:] + (next_word,)
        except (KeyError, IndexError):
            # when we hit a 'dead end' that's alright, we just consider that the end of the 'sentence'
            end_sentence = True

        if _per_sentence_loop_counter >= max_loops_per_sentence:
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


def is_empty_model(model):
    """ Returns True if model is 'empty'
    """
    if not model:
        return True

    if len(model.keys()) == 1:
        # i.e. {('', ..): ['', ..]} (when input is empty string we get this model, and it is best to short-circuit)
        return True

    return False


def ngram_for_sentence_start(ngram_size):
    """ we get better results with special-sentence-start ngram (assuming model & gen use the same one).
    """
    return tuple((START_SYMBOL,) * ngram_size)
