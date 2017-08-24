#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" tests directly against PyMarkovChainFork class (as opposed to the PyMarkovChainTextMaker class, which is preferable)

just a couple because of forking the lib. want to give it smoketests on its own, aside from other
tests related to TextMaker variants. (if something went wrong, it would help pinpoint.)
"""
import os
from collections import namedtuple

import pytest

from presswork.text import grammar
from presswork.text.grammar import rejoin
from presswork.text.markov.thirdparty._pymarkovchain import PyMarkovChainForked

SentencesTestCase = namedtuple('SentencesTestCase', ['text', 'phrase_in_each_sentence'])

# TODO move this test case up to top level conftest as `def text_with_expected_phrase` and it is a UserString
# so there is no confusion about what "type" it is in conftest vs the usage, it can just be used like a string,
# but it does have metadata of .phrase_in_each_sentence, that can be used in asserts.
TEST_CASE_ZEN_OF_PYTHON = SentencesTestCase(
        phrase_in_each_sentence="better than",
        text="""
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
""")


@pytest.fixture
def pymc(tmpdir):
    # note, even though this is using db file, it's using pytest `tmpdir`, so each run gets its own (shouldn't pollute)
    db_file_path = os.path.join(str(tmpdir), "presswork_markov_db")  # TODO get rid of db stuff
    pymc = PyMarkovChainForked(db_file_path=db_file_path)
    return pymc

tokenize = grammar.SentenceTokenizerWhitespace()

@pytest.mark.parametrize(('test_case'), [TEST_CASE_ZEN_OF_PYTHON])
def test_high_level_behavior(pymc, test_case):
    """ Primary acceptance test: does the Markov Chain text maker generate text as expected?

    Text generation with Markov Chains is not deterministic (that's the fun part!)
    so by taking an assumption we can do a test
        assumption: each sentence input has some 2-gram that is the same (i.e. "better than")
        then: even though chance is involved, the 2-gram appears in each output ("better than" in each sentence)

    We also check that each of the "words" (very naively defined) in the output is in the
    original input.
    """
    _sentences = test_case.text.strip().splitlines()
    assert all(test_case.phrase_in_each_sentence in sentence for sentence in _sentences), \
        ("sanity check of test validity failed. expected each sentence in this test case to have a common phrase")

    pymc.database_init(tokenize(test_case.text))

    for x in range(0, len(_sentences) * 3):
        output_text = rejoin(pymc.make_sentences_list(1))
        print output_text
        assert test_case.phrase_in_each_sentence in output_text

        for word in output_text.split():
            assert word in test_case.text


@pytest.mark.parametrize(('test_case'), [TEST_CASE_ZEN_OF_PYTHON])
def test_database_persistence(pymc, test_case):
    assert test_case.phrase_in_each_sentence not in rejoin(pymc.make_sentences_list(1))
    pymc.database_init(tokenize(test_case.text))
    assert test_case.phrase_in_each_sentence in rejoin(pymc.make_sentences_list(1))
    pymc.database_dump()
    pymc.database_clear()
    pymc.database_init(tokenize(test_case.text))
    assert test_case.phrase_in_each_sentence in rejoin(pymc.make_sentences_list(1))

    # dump DB, use another instance to load DB...
    pymc.database_dump()
    # we dumped the DB so another instance w/ same db_file_path argument should behave same.
    text_maker_2 = PyMarkovChainForked(db_file_path=pymc.db_file_path)
    # notice we do not call `database_init` - that doesn't need to happen
    assert test_case.phrase_in_each_sentence in rejoin(text_maker_2.make_sentences_list(1))

    pymc.database_clear()
    # even though we just deleted the db file, db is still in memory...
    assert test_case.phrase_in_each_sentence in rejoin(pymc.make_sentences_list(1))
