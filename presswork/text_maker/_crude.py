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
    # My intention is that, at text_maker module level, you can wire in a better splitter. # TODO make it so
    return tuple(string_of_full_text.splitlines())


def _crude_split_words(string_of_sentence):
    # ATTN: this function is especially crude. it is only left here as a default/fallback.
    # My intention is that, at text_maker module level, you can wire in a better splitter. # TODO make it so
    return tuple(string_of_sentence.split())


def crude_markov_chain(
        # FIXME: this should just take list-of-lists (sentences, words) ; caller should do splitting etc.
        # def make_text(source_text) :
        #       source_text -> sentences_and_words = [[word, ...], [word, ...]] (using composable fns for splitting);
        #       model = chain(sentences_and_words)
        #       <exercise the model>
        # def make_text(model) :
        #       <exercise the model>
        # so yeah pretty easy to see how refactoring to a TextMaker class would help.
        source_text=EXAMPLE_SOURCE,
        ngram_size=DEFAULT_NGRAM_SIZE,
        fn_to_split_sentences=_crude_split_sentences,
        fn_to_split_words=_crude_split_words,
):
    model = {
        (START_SYMBOL * ngram_size): [],
    }

    for sentence in _crude_split_sentences(source_text):
        words = fn_to_split_words(sentence)

        # Ye olde sentence start trick. # TODO(hangtwenty) refactor to helper fn, it's not very DRY right now.
        words_with_padding = ((START_SYMBOL,) * ngram_size) + words + (END_SYMBOL,)

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
        logger.debug('model=\n{}'.format(pprint.pformat(model, width=2)))

    return model


def make_text(model, ngram_size=DEFAULT_NGRAM_SIZE, words_to_generate=100, join_with=" "):
    output_words = []
    current_ngram = None

    # TODO(hangtwenty) it should do a number of *sentences* to generate not number of words.
    for i in xrange(0, words_to_generate + 1):
        if not current_ngram:
            # Ye olde sentence start trick. # TODO(hangtwenty) refactor to helper fn, it's not very DRY right now.
            current_ngram = ((START_SYMBOL,) * ngram_size)

        try:
            next_word_options = model[current_ngram]
            next_word = random.choice(next_word_options)
            output_words.append(next_word)
            current_ngram = current_ngram[1:] + (next_word,)
        except (KeyError, IndexError):
            # "dangling", set current=None, to start new sentence.
            current_ngram = None

    # TODO(hangwenty) should return same list-of-lists ('sentences' and 'words'), leave joining to another caller,
    # such that it could be pluggable.
    return join_with.join(output_words)
