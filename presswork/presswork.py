# -*- coding: utf-8 -*-
"""

Based on: https://pypi.python.org/pypi/PyMarkovChain/
Note from hangtwenty:
    I do NOT take credit for most of this :)
    I just mixed up PyMarkovChain with some NLTK stuff
"""

from __future__ import division
from funcy import collecting
from nltk import TreebankWordTokenizer
import nltk
import regex

try:
    # try to use cPickle for better performance (python2)
    import cPickle as pickle
except ImportError:
    import pickle
import logging
import os
import random
from collections import defaultdict

RE_PUNCTUATION = regex.compile(r'\p{P}')


# <factories>  # Define some factories as functions so we can easily pickle them
def _db_factory():
    """ DB data structure: dict like  {word_sequence: {next_word: probability}}
    """
    return defaultdict(_default_word_probability_dict)


def _default_word_probability_dict():
    """ defaultdict where each key has a value of 1.0 to start with (default probability)

    the keys will be "words"
    """
    return defaultdict(_one)


def _one():
    return 1.0


# </factories>


class EndOfChainException(Exception):
    pass


class WordTokenizer(TreebankWordTokenizer):  # TODO(hangtwenty)
    """ Split text on whitespace and more. `tokenize` method returns a list of words.

    Default tokenizer that works well here is basically Treebank,
    but we neutralize the contractions so that "can't" stays 1 word for example...
    The Ender transformation leaves stopwords in-tact, including contractions,
    so we don't need to decompose "can't" into its two meaningful tokens.
    We don't care. We pass "don't" and "can't" through.
    """
    # TODO(hangtwenty) contractions support - from config file ;)
    # CONTRACTIONS = []

    @collecting
    def tokenize(self, text):
        """
        :rtype: list
        """
        tokens = super(WordTokenizer, self).tokenize(text)
        for token in tokens:
            if RE_PUNCTUATION.match(token):
                yield token
            else:
                yield token


class MarkovChainTextMaker(object):
    DEFAULT_DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "presswork_markov_db")
    DEFAULT_WINDOW_SIZE_WORDS = 2

    # data structure for this db is dictionaries nested 1 deep: `{words: {word: probability}}`
    def __init__(self, db_file_path=None, window=DEFAULT_WINDOW_SIZE_WORDS):
        self.window = window

        # TODO(hangtwenty) get rid of database storage until/unless someone calls dump.

        self.db = None
        self.db_file_path = db_file_path
        if self.db_file_path:
            try:
                with open(self.db_file_path, 'rb') as dbfile:
                    self.db = pickle.load(dbfile)
            except (IOError, ValueError):
                logging.warn('Database file corrupt or not found, using empty database')

        if self.db is None:
            self.db = _db_factory()

        self._word_tokenizer = WordTokenizer()
        self._sentence_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    @classmethod
    def with_persistence(self, db_file_path=DEFAULT_DB_FILE_PATH, **kwargs):
        return MarkovChainTextMaker(db_file_path=db_file_path, **kwargs)

    def increment_words(self, words):
        self.db[("",)][words[0]] += 1

    def database_init(self, text_input_as_string):
        """ Generate word probability database from raw content string """
        # I'm using the database to temporarily store word counts
        text_input_as_string = \
            self._sentence_tokenizer.tokenize(text_input_as_string)
        # We're using the empty string ('') as special symbol for the beginning
        # of a sentence
        self.db[('',)][''] = 0.0
        for line in text_input_as_string:
            words = self._word_tokenizer.tokenize(line)
            if len(words) == 0:
                continue
            # first word follows a sentence end
            self.increment_words(words)

            for order in range(1, self.window + 1):
                for i in range(len(words) - 1):
                    if i + order >= len(words):
                        continue
                    word = tuple(words[i:i + order])
                    self.db[word][words[i + order]] += 1

                # last word precedes a sentence end
                self.db[tuple(words[len(words) - order:len(words)])][""] += 1

        # We've now got the db filled with parametrized word counts
        # We still need to normalize this to represent probabilities
        for word in self.db:
            wordsum = 0
            for nextword in self.db[word]:
                wordsum += self.db[word][nextword]
            if wordsum != 0:
                for nextword in self.db[word]:
                    self.db[word][nextword] /= wordsum

    def database_dump(self):
        try:
            with open(self.db_file_path, 'wb') as dbfile:
                pickle.dump(self.db, dbfile)
            # It looks like db was written successfully
            return True
        except IOError:
            logging.warn('Database file could not be written')
            return False

    def database_clear(self):
        os.unlink(self.db_file_path)

    def make_sentences(self, number):
        sentences = []
        for _ in range(0, number):
            sentences.append(self.make_sentence())
        return "  ".join(sentences)

    def make_sentence(self):
        """ Generate a "sentence" with the database of known text """

        # TODO(hangtwenty) use RE_PUNCTUATION.match() to replace all "<space><punct>" with "<punct>"
        # __or__ make it so that you don't just do " ".join()... and iterate manually, only
        # and only add space between words... (that seems more efficient probably)

        return self._accumulate_with_seed(('',))

    def make_sentence_with_seed(self, seed):
        """ Generate a "sentence" with the database and a given word """
        # using str.split here means we're contructing the list in memory
        # but as the generated sentence only depends on the last word of the seed
        # I'm assuming seeds tend to be rather short.
        words = seed.split()
        if (words[-1],) not in self.db:
            # The only possible way it won't work is if the last word is not known
            raise EndOfChainException('Could not continue string: ' + seed)
        return self._accumulate_with_seed(words)

    def _accumulate_with_seed(self, seed):
        """ Accumulate the generated sentence with a given single word as a
        seed """
        next_word = self._next_word(seed)
        sentence = list(seed) if seed else []
        while next_word:
            sentence.append(next_word)
            next_word = self._next_word(sentence)
        return ' '.join(sentence).strip()

    def _next_word(self, last_words):
        last_words = tuple(last_words)
        if last_words != ('',):
            while last_words not in self.db:
                last_words = last_words[1:]
                if not last_words:
                    return ''
        probmap = self.db[last_words]
        sample = random.random()
        # since rounding errors might make us miss out on some words
        maxprob = 0.0
        maxprobword = ""
        for candidate in probmap:
            # remember which word had the highest probability
            # this is the word we'll default to if we can't find anythin else
            if probmap[candidate] > maxprob:
                maxprob = probmap[candidate]
                maxprobword = candidate
            if sample > probmap[candidate]:
                sample -= probmap[candidate]
            else:
                return candidate
        # getting here means we haven't found a matching word. :(
        return maxprobword
