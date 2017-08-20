# -*- coding: utf-8 -*-
""" 'Legacy' but usable Markov Chain Text Maker class. Based on PyMarkovChain, added NLTK tokenization.

-------------------------------
NOTES RE: AUTHORSHIP & CAVEATS
===============================

Forked from PyMarkovChain library's MarkovChain class (https://pypi.python.org/pypi/PyMarkovChain/).
Markov-Chain implementation details mostly left the same (I do not claim credit),
I forked to bring NLTK into the mix. (Original class did not have good extension points.)

Other implementations may be added soon, and I will consider this one "legacy" ...
For now I am keeping it as a way to compare results from 2+ Markov Chain Text Maker implementations.
Since this codebase is for fun and exploration, I'm keeping it for comparison purposes.

Reviewing a while later, I don't like these things about it:
    - not enough separation of concerns - markov chain, text model, and text maker are all mixed together
    - implementation could be clearer
    - persistence uses pickle (pickle has bad security posture. This is just a toy but still, better to use JSON.)
    - no performance testing or optimization
"""

from __future__ import division

try:
    # try to use cPickle for better performance (python2)
    import cPickle as pickle
except ImportError:
    import pickle

from collections import defaultdict
import logging
import os
import random
import re

from funcy import collecting
from nltk import TreebankWordTokenizer
import nltk

RE_PUNCTUATION = re.compile(ur'\p{P}')
SPECIAL_TOKEN = u''


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


class PyMarkovChainWithNLTK(object):
    """ A text model and text maker in a single class, with options for local filesystem persistence.

    Forked from PyMarkovChain library's MarkovChain class (https://pypi.python.org/pypi/PyMarkovChain/)

    See module header for notes on AUTHORSHIP and CAVEATS.
    """
    # TODO this should use tmpdir
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
        return PyMarkovChainWithNLTK(db_file_path=db_file_path, **kwargs)

    def increment_words(self, words):
        self.db[(SPECIAL_TOKEN,)][words[0]] += 1

    def database_init(self, text_input_as_string):
        """ Generate word probability database from raw content string """
        text_input_as_string = \
            self._sentence_tokenizer.tokenize(text_input_as_string)
        # I'm using the database to temporarily store word counts
        # We need a special symbol for the beginning of a sentence.
        self.db[(SPECIAL_TOKEN,)][SPECIAL_TOKEN] = 0.0
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
                self.db[tuple(words[len(words) - order:len(words)])][SPECIAL_TOKEN] += 1

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
        generated = u"  ".join(sentences)
        return PyMarkovChainWithNLTK.post_process(generated)

    def make_sentence(self):
        """ Generate a "sentence" with the database of known text """
        generated = self._accumulate_with_seed((SPECIAL_TOKEN,))
        return PyMarkovChainWithNLTK.post_process(generated)

    def make_sentence_with_seed(self, seed):
        """ Generate a "sentence" with the database and a given word """
        # using str.split here means we're contructing the list in memory
        # but as the generated sentence only depends on the last word of the seed
        # I'm assuming seeds tend to be rather short.
        words = seed.split()
        if (words[-1],) not in self.db:
            # The only possible way it won't work is if the last word is not known
            raise EndOfChainException(u'Could not continue string: ' + seed)
        generated = self._accumulate_with_seed(words)
        return PyMarkovChainWithNLTK.post_process(generated)

    @staticmethod
    def post_process(string):
        string = PyMarkovChainWithNLTK._remove_space_before_phrase_end_punctuation(string)
        return string

    @staticmethod
    def _remove_space_before_phrase_end_punctuation(string):
        """ Replace " . " with ". ", and so on, for other punctuation that probably ends sentences
        or clauses.
        """
        return re.sub(r'\s([.,!?:;](?:\s|$))', r'\1', string)

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
        if last_words != (SPECIAL_TOKEN,):
            while last_words not in self.db:
                last_words = last_words[1:]
                if not last_words:
                    return SPECIAL_TOKEN
        probmap = self.db[last_words]
        sample = random.random()
        # since rounding errors might make us miss out on some words
        maxprob = 0.0
        maxprobword = SPECIAL_TOKEN
        for candidate in probmap:
            # remember which word had the highest probability
            # this is the word we'll default to if we can't find anything else
            if probmap[candidate] > maxprob:
                maxprob = probmap[candidate]
                maxprobword = candidate
            if sample > probmap[candidate]:
                sample -= probmap[candidate]
            else:
                return candidate
        # getting here means we haven't found a matching word. :(
        return maxprobword
