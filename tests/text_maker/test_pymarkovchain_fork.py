#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO meld this into test_parity, and then it will get refactored later.

"""
test_presswork
----------------------------------

Tests for `presswork` module. Must be run with pytest.

"""
from collections import namedtuple
import os

import pytest

from presswork.text._pymarkovchain_fork import PyMarkovChainWithNLTK

SentencesTestCase = namedtuple('SentencesTestCase', ['text', 'phrase_in_each_sentence'])

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


# TODO more test cases
# TODO test cases for different window/state sizes

@pytest.fixture         # FIXME parametrize this - do both 'raw' and 'wrapped' PyMarkovChainWithNLTK......
def pymc(tmpdir):
    db_file_path = os.path.join(str(tmpdir), "presswork_markov_db")
    pymc = PyMarkovChainWithNLTK.with_persistence(db_file_path)
    return pymc


@pytest.mark.parametrize(('test_case'), [TEST_CASE_ZEN_OF_PYTHON])
def test_high_level_behavior(pymc, test_case):
    """ Primary acceptance test: does the Markov Chain text maker generate text as expected?

    Text generation with Markov Chains is not deterministic (that's the fun part!)
    so by taking an assumption we can do a test
        assumption: each sentence input has some 2-gram that is the same (i.e. "better than")
        then: even though chance is involved, "better than" appears in each output

    We also check that each of the "words" (very naively defined) in the output is in the
    original input.
    """
    _sentences = test_case.text.strip().splitlines()
    assert all(test_case.phrase_in_each_sentence in sentence for sentence in _sentences), \
        ("SentencesTestCase sanity check failed: "
         "a SentencesTestCase should have some phrase in each sentence (line)!")

    pymc.database_init(test_case.text)

    for x in range(0, len(_sentences) * 3):
        output_text = pymc.make_sentence()
        print output_text
        assert test_case.phrase_in_each_sentence in output_text

        for word in output_text.split():
            assert word in test_case.text


def test_post_process():
    res = PyMarkovChainWithNLTK.post_process(
        'foo . bar test : ,! baz ! hi yepyep: blah ; hi')
    assert res == "foo. bar test: ,! baz! hi yepyep: blah; hi"


@pytest.mark.parametrize(('test_case'), [TEST_CASE_ZEN_OF_PYTHON])
def test_database_persistence(pymc, test_case):
    assert test_case.phrase_in_each_sentence not in pymc.make_sentence()
    pymc.database_init(test_case.text)
    assert test_case.phrase_in_each_sentence in pymc.make_sentence()
    pymc.database_dump()
    pymc.database_clear()
    pymc.database_init(test_case.text)
    assert test_case.phrase_in_each_sentence in pymc.make_sentence()

    # dump DB, use another instance to load DB...
    pymc.database_dump()
    # we dumped the DB so another instance w/ same db_file_path argument should behave same.
    text_maker_2 = PyMarkovChainWithNLTK.with_persistence(pymc.db_file_path)
    # notice we do not call `database_init` - that doesn't need to happen
    assert test_case.phrase_in_each_sentence in text_maker_2.make_sentence()

    pymc.database_clear()
    # even though we just deleted the db file, db is still in memory...
    assert test_case.phrase_in_each_sentence in pymc.make_sentence()
