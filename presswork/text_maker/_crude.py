""" Very basic homegrown implementation for fun & reference purposes.

Why it's here:
    - provides a stripped-down reference implementation for understanding the algorithm (which is fundamentally similar
    to the other implementations)
    - provides something to contrast the other implementations with, for testing and benchmarking
    - this whole repository is just for fun and writing this was just for fun.

The implementations in `thirdparty` are preferable for actual usage, outside of development playing-around.
Notable deficiencies:
    - no maturity or battle testing, so haven't found the edge cases yet
    - no optimization of memory usage: instead of storing #s of probabilities, raw lists are used
        (Simplest Thing That Could Possibly Work, demos the essential algorithm, that's all)
    - no optimization of lookups for performance boosts (contrast with jsvine/markovify)
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

# By using empty string as start-of-sentence-marker, we can avoid some sanitization later.
START_SYMBOL = u""


def _markov_chain_of_characters(source_text=EXAMPLE_SOURCE, ngram_size=2):
    model = {}

    for i in xrange(0, len(source_text)):
        ngram = tuple(source_text[i: (i + ngram_size)])

        try:
            follow = source_text[i + ngram_size]
        except IndexError:
            break

        if model.get(ngram, None) is None:
            model[ngram] = [follow]
        else:
            model[ngram].append(follow)

    logger.debug('model=\n{}'.format(pprint.pformat(model, width=2)))
    return model


def markov_chain_of_sentences_and_words(source_text=EXAMPLE_SOURCE, ngram_size=2):
    model = {}

    sentences = source_text.splitlines()  # TODO make sentence-splitting override-able (THAT is why to make it a class)

    for sentence in sentences:
        words = sentence.split()
        for i in xrange(0, len(words)):
            ngram = tuple(words[i:(i + ngram_size)])

            print ngram

            try:
                follow = words[i + ngram_size]
            except IndexError:
                break

            if model.get(ngram, None) is None:
                model[ngram] = [follow.strip()]
            else:
                model[ngram].append(follow.strip())

        logger.debug('model=\n{}'.format(pprint.pformat(model, width=2)))
    return model


def make_text(count_of_words=100, model=None, join_with=" "):
    output_words = []
    current_ngram = None

    for i in range(0, count_of_words):
        if not current_ngram:
            # TODO(hangtwenty) should separate sentence-starts from not, probably, and only use sentence-starts here
            current_ngram = random.choice(model.keys())
            output_words.extend(current_ngram)

        try:
            follow_options = model[current_ngram]
            follow = random.choice(follow_options)
            current_ngram = current_ngram[1:] + (follow,)
            output_words.append(follow)
        except (KeyError, IndexError):
            # "dangling", set current=None, to start new sentence.
            current_ngram = None

    return join_with.join(output_words)


if __name__ == "__main__":
    # result = make_text(model=_markov_chain_of_characters(), join_with="")
    # print result

    result = make_text(model=markov_chain_of_sentences_and_words())
    print result
