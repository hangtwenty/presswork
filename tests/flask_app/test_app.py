# -*- coding: utf-8 -*-
""" minimal Flask app (for now) calls for a minimal test suite (for now)
"""
import bs4
import pytest

from presswork.sanitize import SanitizedString
from presswork.text import grammar
from tests import helpers


@pytest.fixture()
def testapp(request):
    from presswork.flask_app.app import app

    # gen'l Flask note - you CAN keep CSRF protection on in tests (gist.github.com/singingwolfboy/2fca1de64950d5dfed72)
    # but for this toy project that seems like overkill. turning it off
    app.config['WTF_CSRF_ENABLED'] = False

    app.config['DEBUG'] = True
    app.testing = True

    client = app.test_client()

    return client


def test_index_initial_200(testapp):
    """ Tests if the index page loads """

    response = testapp.get('/')
    assert response.status_code == 200


def test_index_submit_deterministic(testapp):
    """ Tests a basic submission """

    # property of markov chain generators: sequence of unique words/tokens has deterministic output
    input_text = 'This is a single sentence with all unique words'
    assert len(input_text.split()) == len(set(input_text.split())), \
        "test self-check failed, this should be all unique words"

    response = testapp.post('/', data=dict(
            input_text=input_text * 10000,
            text_maker_strategy='crude',
            tokenizer_strategy='whitespace',
            ngram_size=2,
            count_of_sentences_to_make=100,
    ))
    assert response.status_code == 200

    generated_text = _get_the_generated_text_from_exact_html_element(response)
    assert input_text in generated_text

    assert "ensure test is valid - this is not in the response data" not in generated_text


@pytest.mark.parametrize('ngram_size', range(2, 4))
@pytest.mark.parametrize('tokenizer_strategy', ['whitespace', 'nltk', 'markovify'])
@pytest.mark.parametrize('text_maker_strategy', ['crude', 'pymc', 'markovify'])
def test_index_submit_thorough(testapp, tokenizer_strategy, text_maker_strategy, ngram_size, text_any):
    """ Tests a submission of various fixtures and various parameters"""
    input_text = text_any
    response = testapp.post('/', data=dict(
            input_text=input_text,
            text_maker_strategy=text_maker_strategy,
            tokenizer_strategy=tokenizer_strategy,
            ngram_size=ngram_size,

            count_of_sentences_to_make=10,
    ))
    assert response.status_code == 200

    generated_text = _get_the_generated_text_from_exact_html_element(response)

    _tokenizer = grammar.create_sentence_tokenizer(tokenizer_strategy)
    comparison = helpers.WordSetComparison(
            generated_tokens=_tokenizer.tokenize(generated_text),
            input_tokenized=_tokenizer.tokenize(SanitizedString(input_text)))
    assert comparison.output_is_subset_of_input


def _get_the_generated_text_from_exact_html_element(response):
    """ helper to get the generated text from the HTML where it is output.

    why parse it by exact HTML element -
        while we could *almost* just use .get_text() on the whole page, the app (may) put the input text back in the
    input text field ... so we could get false-positive matches when looking for generated text.
    """

    response_markup = bs4.BeautifulSoup(response.data, "html.parser")
    generated_text_element = response_markup.find(id="generated-text-body")
    assert generated_text_element

    generated_text = generated_text_element.get_text(separator="\n\n")
    assert len(generated_text.strip()) > 1

    return generated_text


def test_invalid_strategies_chosen(testapp):
    # valid
    response = testapp.post('/', data=dict(
            input_text="yada yada",
            text_maker_strategy="pymc",  # valid
            tokenizer_strategy="whitespace",  # valid
            ngram_size=2,
            count_of_sentences_to_make=1,
    ))
    assert not "warning" in response.data, "self-check failed, test case cannot proceed"

    # invalid
    response = testapp.post('/', data=dict(
            input_text="yada yada",
            text_maker_strategy="pymc",  # valid
            tokenizer_strategy="invalid",  # invalid
            ngram_size=2,
            count_of_sentences_to_make=1,
    ))

    assert "warning" in response.data

    # invalid
    response = testapp.post('/', data=dict(
            input_text="yada yada yada",
            text_maker_strategy="invalid",  # invalid
            tokenizer_strategy="whitespace",  # valid
            ngram_size=2,
            count_of_sentences_to_make=1,
    ))

    assert "warning" in response.data

    # invalid
    response = testapp.post('/', data=dict(
            input_text="yada yada yada",
            text_maker_strategy="invalid",  # valid
            tokenizer_strategy="whitespace",  # valid
            ngram_size="\x02",
            count_of_sentences_to_make=1,
    ))

    assert "warning" in response.data
