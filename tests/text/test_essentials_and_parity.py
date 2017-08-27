# -*- coding: utf-8 -*-
""" test TextMaker variants - esp. essential properties of markov chain text generators, and parity of the strategies
"""
import pytest

import presswork.text.grammar
from presswork.text import grammar
from presswork.text import text_makers
from presswork.text.markov import _crude_markov
from presswork.utils import iter_flatten

from tests import helpers


def test_smoketest_common_phrase(each_text_maker):
    """ smoketest: given input with same phrase in each sentence, expect that phrase in each output sentence.

    :param each_text_maker: each text maker, injected by pytest from each_text_maker fixture.
    """
    text = ("Beautiful is better than ugly.\n" +
            "Explicit is better than implicit.\n" +
            "Simple is better than complex.\n" +
            "Complex is better than complicated.\n" +
            "Flat is better than nested.\n" +
            "Sparse is better than dense.")

    text_maker = each_text_maker
    text_maker.input_text(text)
    sentences = text_maker.make_sentences(1000)
    for sentence in sentences:
        assert "is better than" in " ".join(sentence)


@pytest.mark.parametrize('ngram_size', range(2, 6))
@pytest.mark.parametrize('joiner', map(grammar.create_joiner, grammar.JOINER_NICKNAMES))
@pytest.mark.parametrize('sentence_tokenizer', [
    grammar.SentenceTokenizerNLTK(word_tokenizer=grammar.WordTokenizerNLTK()),
    grammar.SentenceTokenizerNLTK(word_tokenizer=grammar.WordTokenizerWhitespace()),
])
def test_essential_properties_of_text_making(each_text_maker, ngram_size, sentence_tokenizer, joiner, text_any):
    """ confirm some essential known properties of text-making output, common to all the text makers

    :param each_text_maker: each text maker, injected by pytest from each_text_maker fixture.
    :param ngram_size: passed to text maker, here we test a 'reasonable' range (other cases test bigger range)
    :param sentence_tokenizer:  in practice the tokenizer choice is significant, however in test case we just try each.
        when tokenizer is same on input & output, it 'cancels out'.
        so we can take this opportunity to exercise many tokenizers, and affirm mix-and-match-ability
    :param text_any: a fixture from conftest.py: 1 at a time, will be each fixture from tests/fixtures/plaintext
    """
    text_maker = each_text_maker
    text_maker.ngram_size = ngram_size
    text_maker.sentence_tokenizer = sentence_tokenizer

    _input_tokenized = text_maker.input_text(text_any)

    sentences = text_maker.make_sentences(300)

    word_set_comparison = helpers.WordSetComparison(generated_tokens=sentences, input_tokenized=_input_tokenized)
    assert word_set_comparison.output_is_valid_strict()


@pytest.mark.parametrize('sentence_tokenizer', [
    grammar.SentenceTokenizerWhitespace(word_tokenizer=grammar.WordTokenizerWhitespace()),
    grammar.SentenceTokenizerWhitespace(word_tokenizer=grammar.WordTokenizerNLTK()),
    grammar.SentenceTokenizerMarkovify(),
])
def test_text_making_with_blankline_tokenizer(each_text_maker, sentence_tokenizer, text_newlines):
    """ covers some of same ground as test_essential_properties, but uses tokenizer that only works with line-separated

    :param text_newlines: 1 text at a time, but only fixture(s) where it is (mostly) newline separated
    """
    text_maker = each_text_maker
    text_maker.sentence_tokenizer = sentence_tokenizer

    _input_tokenized = text_maker.input_text(text_newlines)
    sentences = text_maker.make_sentences(200)

    word_set_comparison = helpers.WordSetComparison(generated_tokens=sentences, input_tokenized=_input_tokenized)

    assert word_set_comparison.output_is_valid_strict()

    # as a followup, let's double check that our comparison is valid (by confirming invalidated case would fail)
    _test_self_ensure_test_would_fail_if_comparison_was_invalid(
            generated_tokens=sentences, input_tokenized=_input_tokenized)


@pytest.mark.parametrize('ngram_size', range(2, 12))
def test_easy_deterministic_cases_are_same_for_all_text_makers(all_text_makers, text_easy_deterministic, ngram_size):
    """ Any TextMaker will return deterministic results from seq of words w/ no duplicates; all strategies should match

    (btw high ngram_sizes aren't very useful, but included here because sparks should not fly...!)
    """
    outputs = {}
    for text_maker in all_text_makers:
        text_maker.ngram_size = ngram_size
        text_maker.input_text(text_easy_deterministic)

        outputs[text_maker.NICKNAME] = text_maker.make_sentences(1)

    # expected is that all text makers output same deterministic sentence for these inputs.
    # we can check that pretty elegantly by stringifying, calling set, and making sure their is only 1 unique output
    # (temporary dict var is not necessary for assertion - is just for ease of debugging when something goes wrong)
    outputs_rejoined = {name: grammar.JoinerWhitespace().join(output).strip() for name, output in outputs.items()}
    assert len(set(outputs_rejoined.values())) == 1


def test_empty_and_null(each_text_maker, empty_or_null_string):
    """ covers some of same ground as test_essential_properties, but uses tokenizer that only works with line-separated

    :param text_newlines: 1 text at a time, but only fixture(s) where it is (mostly) newline separated
    """
    text_maker = each_text_maker
    text_maker.input_text(empty_or_null_string)
    sentences = text_maker.make_sentences(10)
    assert sentences is not None

    # how each text maker handles empty strings or no-op whitespace - is un-defined, and intentionally "liberal,"
    # basically deferring any cleanup etc until final re-join. so,
    # each text maker is free to return [[],[],[]] vs [[''],['']] etc, BUT... we *DO* have an assertable expectation
    # in this case, that when you flatten-and-filter, it should reduce to empty i.e. []
    assert not filter(None, iter_flatten(sentences))


def _test_self_ensure_test_would_fail_if_comparison_was_invalid(generated_tokens, input_tokenized):
    """ for posterity, let's add a self-check to make sure failure WOULD happen when it should.

    given comparison test has already passed - generate_tokens *ARE* subset of input_tokenized -
    then we can take those valid args, and invalidate them, by throwing erroneous token onto generated_tokens.
    this should fail, confirming test would fail if something was off.
    """
    invalid_word_set_comparison = helpers.WordSetComparison(
            generated_tokens=generated_tokens + ["XXXXXXXXX_This_Token_Is_Not_In_Any_Input_Text_XXXXXXXXX"],
            input_tokenized=input_tokenized)
    assert not invalid_word_set_comparison.output_is_valid_strict()
    return True


def test_sentence_starts_are_special(each_text_maker, text_newlines):
    """ rules of markov chains for text gen, as these 3 strategies do it anyways - sentence starts are special

    (in a very early version this rule got violated for a bit, so this is a regression test)
    """
    tm = each_text_maker
    input_tokenized = tm.input_text(text_newlines)
    gen_sentences = tm.make_sentences(100)
    gen_starts = [filter(None, sentence)[0] for sentence in gen_sentences]
    input_starts = [filter(None, sentence)[0] for sentence in input_tokenized]
    for start in gen_starts:
        assert start in input_starts


# ------------------------------------------------------------------------------------------------
# Following tests are more about avoiding usage issues (more than properties of the text making)
# ================================================================================================
def test_locked_after_input_text(each_text_maker):
    tm = each_text_maker
    tm.input_text("Foo bar baz. Foo bar quux.")

    with pytest.raises(text_makers.TextMakerIsLockedException):
        tm.input_text("This should not be loaded")

    with pytest.raises(text_makers.TextMakerIsLockedException):
        tm.clone()  # can't clone() after input either, just in case that could cause astonishing state bugs

    output = tm.make_sentences(50)

    assert "This" not in tm.join(output)
    assert "loaded" not in tm.join(output)


def test_cannot_change_ngram_size_after_inputting_text(each_text_maker):
    text_maker = each_text_maker
    text_maker.ngram_size = 4  # this is allowed, it is not locked yet...

    text_maker.input_text("Foo bar blah baz. Foo bar blah quux.")
    with pytest.raises(text_makers.TextMakerIsLockedException):
        text_maker.ngram_size = 3


def test_avoid_pollution_between_instances(each_text_maker):
    """ helps to confirm a design goal - of the instances being isolated, despite issues with underlying strategies

    two ways pollution between the instances could happen (both observed with PyMarkovChain for example):
        a) both sharing same disk persistence for the model, too automatically (now disabled)
        b) if not careful about how 2+ are set up/copied, ".strategy" could be pointer to same instance of underlying
        strategy - TextMaker.copy() added to help avoid this

    so this test case avoids regressions in (a) mainly. point (b) is helpful to this test case and normal usage,
    so might as well exercise it here
    """
    text_maker_1 = each_text_maker
    text_maker_2 = text_maker_1.clone()

    text_maker_1.input_text("Foo bar baz. Foo bar quux.")
    text_maker_2.input_text("Input text for 2 / Input text does not go to 1 / class does not share from 1")

    assert 'Foo' in str(text_maker_1.make_sentences(10))
    assert 'Foo' not in str(text_maker_2.make_sentences(10))

    assert 'Input' in str(text_maker_2.make_sentences(10))
    assert 'Input' not in str(text_maker_1.make_sentences(10))


def test_factory_special_cases():
    """ this already gets exercised in other tests, for the most part, but let's cover a few more cases
    """
    # happy path (not special, but always like to have a counter-example in a test case...)
    assert text_makers.create_text_maker()
    assert text_makers.create_text_maker(
            "crude", sentence_tokenizer="just_whitespace", joiner="just_whitespace", ngram_size=10)

    class MyCustomTextMaker(text_makers.TextMakerCrude):
        pass

    my_custom_text_maker = text_makers.create_text_maker(
            MyCustomTextMaker, sentence_tokenizer="just_whitespace", joiner="just_whitespace")

    assert isinstance(my_custom_text_maker, MyCustomTextMaker)

    # onto some invalid ones
    with pytest.raises(ValueError):
        text_makers.create_text_maker(None)

    with pytest.raises(KeyError):
        text_makers._get_text_maker_class("invalid_nickname")

    with pytest.raises(KeyError):
        text_makers.create_text_maker("invalid_nickname")

    with pytest.raises(KeyError):
        text_makers.create_text_maker(sentence_tokenizer="invalid")

    with pytest.raises(KeyError):
        text_makers.create_text_maker(joiner="invalid")

    with pytest.raises(KeyError):
        text_makers.create_text_maker(joiner="invalid")

    # valid - passing in a tokenizer, which is just defined as something that implements tokenize()
    # notice that it doesn't subclass - duck typing should strictly care about that
    class SomeCustomTokenizer(object):
        def tokenize(self, text):
            return [[word.strip() for word in sent.split()] for sent in text.splitlines()]

    text_input = "woohoo that tokenizer quacks like a duck"
    tm = text_makers.create_text_maker(sentence_tokenizer=SomeCustomTokenizer())
    tm.input_text("woohoo that tokenizer quacks like a duck")
    assert tm.join(tm.make_sentences(1)) == text_input

    # not valid
    with pytest.raises(ValueError):
        text_makers.create_text_maker(sentence_tokenizer=lambda x: x)

    # not valid - passing in some other instances that don't "quack" right/ don't implement required methods
    with pytest.raises(ValueError):
        text_makers.create_text_maker(sentence_tokenizer=object())
    with pytest.raises(ValueError):
        text_makers.create_text_maker(joiner=object())


def test_mismatched_ngram_size_for_crude():
    # quick test for a failure mode that is important, but wasn't covered before
    ngram_size = 2
    tokenize = grammar.SentenceTokenizerWhitespace().tokenize
    model = _crude_markov.crude_markov_chain(
            sentences_as_word_lists=tokenize("foo bar baz"),
            ngram_size=ngram_size)

    with pytest.raises(ValueError):
        generator = _crude_markov.iter_make_sentences(model, count=10, ngram_size=ngram_size + 1)
        generator.next()
