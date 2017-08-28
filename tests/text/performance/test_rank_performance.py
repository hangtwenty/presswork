""" some very rough performance comparisons - get a rough sense of what is fastest

these are disabled by default. to run these, pass "--runslow" to py.test. will be run by `make test-all` or `tox`, too.

- these ARE NOT valid "benchmarks" ... really just misusing the pytest-benchmark library as a way to conveniently
performance test the markov chain strategies, & _LOOSELY_ rank them in speed.

    - the text-making is probabilistic ... and even if we mock `random`, each strategy might do more or fewer runs,
    just based on how things shake out for their own model. unless we really contrive input to avoid that,
    however then that's another way it's not a very useful test! basically it's hard to end up comparing apples to
    apples fully, while also having the test be meaningful in the problem domain.

    - so for the input text in this case, it seems best best if it's not 100% deterministic, but is *mostly*
    deterministic up until the last part of the sentences. this makes it so each strategy will *tend* to do similar
    amounts of runs, slightly better comparison

even so... loose ranking is nice to have.
"""
import pytest

ends = """
Furiously
Financially
Willfully
Abruptly
Endlessly
Firmly
Delightfully
Quickly
Lightly
Eternally
Delicately
Wearily
Sorrowfully
Beautifully
Truthfully
""".split()

input_text = "\n".join(["Colorless green ideas sleep {}".format(end) for end in ends])


@pytest.mark.slow
@pytest.mark.parametrize('ngram_size', range(2, 6))
def test_benchmarks(each_text_maker, ngram_size, benchmark):
    text_maker = each_text_maker
    text_maker.ngram_size = ngram_size
    text_maker.input_text(input_text)

    def wrapped():
        return text_maker.make_sentences(50)

    # outputs[text_maker.NICKNAME] = text_maker.make_sentences(1)
    benchmark.pedantic(wrapped, iterations=10, rounds=100)
