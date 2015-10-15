#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_presswork
----------------------------------

Tests for `presswork` module. Must be run with pytest.

"""
from collections import namedtuple
import os
import pytest

from presswork import presswork

SentencesTestCase = namedtuple('SentencesTestCase', ['text', 'phrase_in_each_sentence'])

CASE_A = SentencesTestCase(
    text="""
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
""", phrase_in_each_sentence="better than")

TEXT_INPUT_MED = """
Beautiful is better than ugly.
Explicit is better than implicit.
Simple is better than complex.
Complex is better than complicated.
Flat is better than nested.
Sparse is better than dense.
Readability counts.
Special cases aren't special enough to break the rules.
Although practicality beats purity.
Errors should never pass silently.
Unless explicitly silenced.
In the face of ambiguity, refuse the temptation to guess.
There should be one-- and preferably only one --obvious way to do it.
Although that way may not be obvious at first unless you're Dutch.
Now is better than never.
Although never is often better than *right* now.
If the implementation is hard to explain, it's a bad idea.
If the implementation is easy to explain, it may be a good idea.
Namespaces are one honking great idea -- let's do more of those!
"""


# noinspection PyUnresolvedReferences
@pytest.fixture
def text_maker(tmpdir):
    db_file_path = os.path.join(str(tmpdir), "presswork_markov_db")
    text_maker = presswork.MarkovChainTextMaker(db_file_path=db_file_path)
    return text_maker

# @pytest.mark.parametrize((''))
def test_high_level_behavior(text_maker):#, sentences_case):
    """ Primary cceptance test: does the Markov Chain text maker generate text as expected?

    Text generation with Markov Chains is not deterministic (that's the fun part!)
    so we test by
        (a) ensuring each sentence input has some key phrase, so that the model
            always ends up using this key phrase in its output and then
        (b) asserting that key phrase is indeed in the output.

    We also check that each of the "words" (very naïvely defined) in the output is in the
    original output. That'll always be true.
    """
    sentences_case = CASE_A
    _sentences = sentences_case.text.strip().splitlines()
    assert all(sentences_case.phrase_in_each_sentence in sentence for sentence in _sentences), \
        ("SentencesTestCase sanity check failed: "
         "a SentencesTestCase should have some phrase in each sentence (line)!")

    # TODO(hangtwenty) parametrize on "sentences_case"
    text_maker.database_init(sentences_case.text)

    for x in range(0, len(_sentences) * 3):
        output_text = text_maker.make_sentence()
        print output_text
        assert sentences_case.phrase_in_each_sentence in output_text

        for word in output_text.split():
            assert word in sentences_case.text


def test_database_persistence(text_maker):
    sentences_case = CASE_A
    assert sentences_case.phrase_in_each_sentence not in text_maker.make_sentence()
    text_maker.database_init(sentences_case.text)
    assert sentences_case.phrase_in_each_sentence in text_maker.make_sentence()
    text_maker.database_dump()
    text_maker.database_clear()
    text_maker.database_init(sentences_case.text)
    assert sentences_case.phrase_in_each_sentence in text_maker.make_sentence()

    # dump DB, use another instance to load DB...
    text_maker.database_dump()
    # we dumped the DB so another instance w/ same db_file_path argument should behave same.
    text_maker_2 = presswork.MarkovChainTextMaker.with_persistence(text_maker.db_file_path)
    # notice we do not call `database_init` - that doesn't need to happen
    assert sentences_case.phrase_in_each_sentence in text_maker_2.make_sentence()

    text_maker.database_clear()
    # even though we just deleted the db file, db is still in memory...
    assert sentences_case.phrase_in_each_sentence in text_maker.make_sentence()


if __name__ == '__main__':
    unittest.main()
