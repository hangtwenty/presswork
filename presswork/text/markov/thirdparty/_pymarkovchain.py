# -*- coding: utf-8 -*-
""" 'Legacy' but usable Markov Chain Text Maker class. Forked from PyMarkovCHain

------------------------------------------------------------------------------------------------------------
NOTES RE: AUTHORSHIP & CAVEATS
============================================================================================================

Forked from PyMarkovChain==1.7.5 MarkovChain class
(https://github.com/TehMillhouse/PyMarkovChain/tree/ade01f64b6107e426f6c01168aae14ad238c656f).
Its algorithm is left the (mostly) same, though I did refactor some things after forking.

I originally forked it to bring NLTK into the mix for tokenizing (Original class did not have good extension points.)
... but now, have hollowed it out further.

Markovify is preferable for most uses but this implementation is kept here as a contrast or fallback.
(Since this repo is non-utilitarian anyways. Nice excuse eh!)
"""

from __future__ import division

from presswork import constants

try:
    # try to use cPickle for better performance (python2)
    import cPickle as pickle
except ImportError: # pragma: no cover
    import pickle

from collections import defaultdict
import logging
import os
import random

import warnings

SPECIAL_TOKEN = u''



def _db_factory():
    """ DB data structure: dict like  {word_sequence: {next_word: probability}}
    """
    return defaultdict(_default_word_probability_dict)


def _default_word_probability_dict():
    """ defaultdict where each key has a value of 1.0 to start with (default probability)

    data structure for PyMarkovChain model: dictionaries nested 1 deep: `{ngram: {next_word: probability, ...}, ...}`
    """
    return defaultdict(_one)


def _one():
    return 1.0


class EndOfChainException(Exception):
    pass


class PyMarkovChainForked(object):
    """ A text model and text maker in a single class, with options for local filesystem persistence.

    Forked from PyMarkovChain library's MarkovChain class (https://pypi.python.org/pypi/PyMarkovChain/)

    See module header for notes on AUTHORSHIP and CAVEATS.
    """
    # TODO this should use tmpdir
    DEFAULT_DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "presswork_markov_db")
    DEFAULT_WINDOW_SIZE_WORDS = constants.DEFAULT_NGRAM_SIZE

    def __init__(
            self,
            db_file_path=None,
            window=DEFAULT_WINDOW_SIZE_WORDS,
    ):
        self.window = window

        self.db = None
        self.db_file_path = db_file_path
        self.load_db_pickle_from_filepath()

        if self.db is None:
            self.db = _db_factory()

    def load_db_pickle_from_filepath(self):
        warnings.warn("Features of PyMarkovChainFork managing its own persistence are deprecated.")
        if self.db_file_path:
            try:
                with open(self.db_file_path, 'rb') as dbfile:
                    self.db = pickle.load(dbfile)
            except (IOError, ValueError):  # pragma: no cover
                logging.debug('db_file_path given, but unreadable (not found, or corrupt), using empty database')

    @property
    def _special_ngram(self):
        # The original PyMarkovChain implementation used this as a beginning (regardless of ngram size)
        # ... I consider this "legacy" so I'm treading lightly in some ways, i.e. not removing this convention,
        # ... however I wanted to DRY up the usages a little.
        return (SPECIAL_TOKEN,)

    def increment_words(self, words):
        self.db[self._special_ngram][words[0]] += 1

    def database_init(self, sentences_as_word_lists):
        """ Generate word probability database from raw content string """

        # (Comment from original:) using the database to temporarily store word counts
        # (Comment from original:) We need a special symbol for the beginning of a sentence.
        self.db[self._special_ngram][SPECIAL_TOKEN] = 0.0
        for word_seq in sentences_as_word_lists:
            if len(word_seq) == 0:
                continue
            # (Comment from original:) first word follows a sentence end
            self.increment_words(word_seq)

            for order in range(1, self.window + 1):
                for i in range(len(word_seq) - 1):
                    if i + order >= len(word_seq):
                        continue
                    word = tuple(word_seq[i:i + order])
                    self.db[word][word_seq[i + order]] += 1

                # (Comment from original:) last word precedes a sentence end
                self.db[tuple(word_seq[len(word_seq) - order:len(word_seq)])][SPECIAL_TOKEN] += 1

        # (Comment from original:) We've now got the db filled with parametrized word counts
        # (Comment from original:) We still need to normalize this to represent probabilities
        for word in self.db:
            wordsum = 0
            for nextword in self.db[word]:
                wordsum += self.db[word][nextword]
            if wordsum != 0:
                for nextword in self.db[word]:
                    self.db[word][nextword] /= wordsum

    def database_dump(self):
        warnings.warn("Features of PyMarkovChainFork managing its own persistence are deprecated.")
        try:
            with open(self.db_file_path, 'wb') as dbfile:
                pickle.dump(self.db, dbfile)
            # It looks like db was written successfully
            return True
        except IOError:
            logging.warn('Database file could not be written')
            return False

    def database_clear(self):
        warnings.warn("Features of PyMarkovChainFork managing its own persistence are deprecated.")
        os.unlink(self.db_file_path)

    def make_sentences_list(self, number):
        seed = self._special_ngram      # (removed ability to pass in custom seed; was not in use by presswork)

        sentences = []
        for _ in range(0, number):
            sentences.append(self._generate_sentence_as_list(seed))

        return sentences

    def _generate_sentence_as_list(self, seed):
        """ Accumulate the generated sentence with a given single word as a seed """
        next_word = self._next_word(seed)
        sentence = list(seed) if seed else []
        while next_word:
            sentence.append(next_word)
            next_word = self._next_word(sentence)
        return sentence

    def _next_word(self, last_words):
        last_words = tuple(last_words)
        if last_words != self._special_ngram:
            while last_words not in self.db:
                last_words = last_words[1:]
                # I don't feel guilty putting "pragma: no cover" on next line as it is a failsafe;
                # my tests don't hit it, and maybe it never gets hit, but it's not *in*correct behavior
                if not last_words:  # pragma: no cover
                    return SPECIAL_TOKEN
        probmap = self.db[last_words]
        sample = random.random()
        # (Comment from original:) since rounding errors might make us miss out on some words
        maxprob = 0.0
        maxprobword = SPECIAL_TOKEN
        for candidate in probmap:
            # (Comment from original:) remember which word had the highest probability
            # (Comment from original:) this is the word we'll default to if we can't find anything else
            if probmap[candidate] > maxprob:
                maxprob = probmap[candidate]
                maxprobword = candidate
            if sample > probmap[candidate]:
                sample -= probmap[candidate]
            else:
                return candidate
        # getting here means we haven't found a matching word. :(
        return maxprobword
