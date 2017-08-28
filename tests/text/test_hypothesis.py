""" dabbling in some property-based testing with Hypothesis.

Very nice to run locally. It tries to give all sorts of bad or difficult inputs >:-)

When it runs:
- Hypothesis docs recommend not to run it on CI, so we do not.
- Marked with "slow" so it only runs if "--runslow" is given. (If you run `tox` locally, or `make test-all`, it'll run.)

http://hypothesis.readthedocs.io/en/latest/quickstart.html
http://hypothesis.readthedocs.io/en/latest/data.html
"""
import os

import pytest
from hypothesis import given
from hypothesis.strategies import text

from tests import helpers


@pytest.mark.slow
@pytest.mark.skipif("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", reason="Skip this test on CI.")
@given(s=text(min_size=10))
def test_hypothesis_text(s, each_text_maker):
    # have to get a fresh text maker EACH time function is invoked, due to Hypothesis quirk explained here:
    # http://hypothesis.works/articles/hypothesis-pytest-fixtures/
    text_maker = each_text_maker.clone()

    _input_tokenized = text_maker.input_text(s)

    sentences = text_maker.make_sentences(300)

    word_set_comparison = helpers.WordSetComparison(generated_tokens=sentences, input_tokenized=_input_tokenized)
    assert word_set_comparison.output_is_valid_strict()
