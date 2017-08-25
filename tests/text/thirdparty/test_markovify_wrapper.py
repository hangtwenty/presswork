"""

this module should NOT test all of Markovify -
    - Markovify already has a test suite,
    - Markovify & our adapter (MarkovifyLite) get exercised plenty in text.text_makers

what's left is just to test the edges
"""
import collections

from presswork.text.markov.thirdparty import _markovify

quick_dirty_tokenize = lambda text: [[word.strip() for word in sent.split()] for sent in text.splitlines()]


def test_markovify_doesnt_stringify_too_soon(text_easy_deterministic):
    input_text = "Colorless green ideas sleep furiously."
    markovify_lite = _markovify.MarkovifyLite(parsed_sentences=quick_dirty_tokenize(input_text))

    assert markovify_lite.make_sentence()

    # Markovify itself stringifies before returning. Confirm we have disabled that
    assert not isinstance(markovify_lite.make_sentence(), basestring)
    assert isinstance(markovify_lite.make_sentence(), collections.Container)
