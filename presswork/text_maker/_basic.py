""" Very basic homegrown implementation for fun & illustration purposes.

Also serves as a "strawman" that is less accurate, with worse memory usage and performance, than the others.
Will provide a contrast in testing.
"""

# TODO doctests where it makes sense. (don't forget to add --doctest-modules to tox.ini etc)

import pprint
import random

SOURCE = u"""
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
"""

START = "^"

def markov_chain_of_chars(source_text=SOURCE, ngram_size=2):
    model = {}

    for i, char in enumerate(source_text):
        ngram = tuple(source_text[i:i+ngram_size])

        try:
            follow = source_text[i + ngram_size]
        except IndexError:
            break

        if model.get(ngram, None) is None:
            model[ngram] = [follow]
        else:
            model[ngram].append(follow)

    pprint.pprint(model)
    return model


def markov_chain_of_sentences_and_words(source_text=SOURCE, ngram_size=2):
    model = {}

    sentences = source_text.splitlines()

    for sentence in sentences:
        words = sentence.split()
        for i, __ in enumerate(words):
            ngram = tuple(words[i : (i + ngram_size)])

            print ngram

            try:
                follow = words[i + ngram_size]
            except IndexError:
                break

            if model.get(ngram, None) is None:
                model[ngram] = [follow.strip()]
            else:
                model[ngram].append(follow.strip())

        pprint.pprint(model)
    return model


def make_text(count=1000, model=None, join_with=" "):
    output = []
    current = None

    for i in range(0, count):
        if not current:
            current = random.choice(model.keys())
            output.extend(current)

        try:
            follow_options = model[current]
            follow = random.choice(follow_options)
            current = current[1:] + (follow,)
            output.append(follow)
        except (KeyError, IndexError):
            # "dangling", set current=None, to start new sentence.
            current = None

    print join_with.join(output)


if __name__ == "__main__":
    make_text(model=markov_chain_of_chars(), join_with="")
    make_text(model=markov_chain_of_sentences_and_words())

