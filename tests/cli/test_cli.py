#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests for presswork CLI

doesn't re-hash same checks from test_essentials_and_parity - moreso testing integration between the CLI and the
text makers. as well as some behavior/interface aspects of the CLI.
"""

from mock import patch
import pytest

from click.testing import CliRunner

from presswork import cli
from presswork.text import grammar

from tests import helpers


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.parametrize('ngram_size', [2, 3])
@pytest.mark.parametrize('input_encoding', ['utf-8', 'raw'])
def test_cli_large_input_from_stdin(runner, text_newlines, ngram_size, input_encoding):
    """ take in text fixture(s)... should be able to gobble up books no issue. from stdin too.
    """

    # Click's CliRunner is very useful, but does seem to choke when "input=" (stdin) parameter is not perfectly
    # encoded. we want other parts of the code, such as direct TextMaker usage, to consume anything thrown at it,
    # but it OK if the CLI expects clean/precise encodings. so we streamroll a bit here, but it's OK for *this* test.
    input_text = unicode(text_newlines, encoding='utf-8', errors='replace')

    tokenizer_strategy = 'just_whitespace'
    result = runner.invoke(cli.main, catch_exceptions=False, input=input_text, args=[
        '--input-filename', '-',
        '--input-encoding', input_encoding,
        '--tokenize', tokenizer_strategy,
        '--join', 'nltk',
        '--ngram-size', ngram_size,
    ])

    output_text = result.output.strip()

    comparison = helpers.FrontendWordSetComparison.create(
            generated_text=output_text,
            input_text=input_text,
            tokenizer=grammar.create_sentence_tokenizer(tokenizer_strategy))

    assert comparison.output_is_valid_strict()


@pytest.mark.parametrize("strategy", ['markovify', 'pymc', 'crude'])
@pytest.mark.parametrize("tokenizer_strategy", grammar.TOKENIZER_NICKNAMES)
@pytest.mark.parametrize("joiner_strategy", grammar.JOINER_NICKNAMES)
@pytest.mark.parametrize('input_encoding', ['utf-8', 'raw'])
def test_cli_large_input_from_file(
        runner, text_newlines, strategy, joiner_strategy, tokenizer_strategy, input_encoding):
    """ take in text fixture(s)... should be able to gobble up books no issue. from files by filename
    """
    input_filename = text_newlines.filename
    input_text = text_newlines

    result = runner.invoke(cli.main, catch_exceptions=False, args=[
        '--input-filename', input_filename,
        '--input-encoding', input_encoding,
        '--strategy', strategy,
        '--tokenize', tokenizer_strategy,
        '--join', joiner_strategy,
        '--ngram-size', 2,
        '--count', 100
    ])
    output_text = result.output.strip()
    assert output_text

    comparison = helpers.FrontendWordSetComparison.create(
            generated_text=output_text,
            input_text=input_text,
            tokenizer=grammar.create_sentence_tokenizer(tokenizer_strategy))

    assert comparison.output_is_mostly_valid(tolerance=(1.0 / 100))


def test_cli_default_strategy(runner):
    """ tests the ease-of-use requirement for the CLI, that with no --strategy arg, some default MC behavior happens.
    """
    result = runner.invoke(cli.main, input="Foo is better than bar. Foo is better than baz.", catch_exceptions=False)
    assert result.exit_code == 0
    assert 'better than' in result.output


def test_cli_choose_strategy(runner):
    stdin = "a b c d a b c x"

    # positive case
    with patch(target="presswork.text.text_makers.TextMakerCrude.input_text") as mock:
        result = runner.invoke(cli.main, input=stdin, args=["--strategy", "crude"], catch_exceptions=False)
        assert result.exit_code == 0
        assert mock.called

    # another positive case
    with patch(target="presswork.text.text_makers.TextMakerPyMarkovChain.input_text") as mock:
        result = runner.invoke(cli.main, input=stdin, args=["--strategy", "pymc"], catch_exceptions=False)
        assert result.exit_code == 0
        assert mock.called

    # negative case as sanity check - if invalid strategy the method would NOT be called
    with patch(target="presswork.text.text_makers.TextMakerPyMarkovChain.input_text") as mock:
        runner.invoke(cli.main, input=stdin, args=["--strategy", "unknown"], catch_exceptions=True)
        assert not mock.called

    with patch(target="presswork.text.text_makers.TextMakerMarkovify._lock", autospec=True) as mock:
        # nitty gritty detail -- Due to quirk of Markovify and how we had to wrap it, mocking input_text()
        # actually breaks it. general mock thing: if you mock an instance method, it'll no longer have side effects
        # on instance(s). it's kind of like you'd turned them into a static method etc.
        # but the good part is, in this test case, we don't care. just checking the wiring is there, from CLI to class.
        # so, instead of mocking input_text, we can mock _lock & get same assurance, just different means
        result = runner.invoke(cli.main, input=stdin, args=["--strategy", "markovify"], catch_exceptions=False)
        assert result.exit_code == 0
        assert mock.called


@pytest.mark.parametrize("strategy", ['markovify', 'pymc', 'crude'])
@pytest.mark.parametrize("tokenizer_strategy", grammar.TOKENIZER_NICKNAMES)
@pytest.mark.parametrize("joiner_strategy", grammar.JOINER_NICKNAMES)
def test_cli_empty_inputs(runner, strategy, joiner_strategy, tokenizer_strategy, empty_or_null_string):
    """ confirm nothing too weird happens from empty inputs or inputs of control chars like null byte etc

    (these inputs used to break the CLI! so this is a regression test.)
    """
    stdin = empty_or_null_string
    result = runner.invoke(cli.main, input=stdin, catch_exceptions=False, args=[
        '--strategy', strategy,
        '-j', joiner_strategy,
        '-t', tokenizer_strategy
    ])
    assert result.exit_code == 0
    assert result.output.strip() == ''


def test_cli_invalid_strategies(runner):
    # valid
    result = runner.invoke(cli.main, input="Foo bar foo baz")
    assert result.exit_code == 0

    # invalid
    result = runner.invoke(cli.main, input="Foo bar foo baz", args=['--strategy', 'invalid'])
    # (side note, it is odd that Click library uses 2 for invalid choices (http://tldp.org/LDP/abs/html/exitcodes.html)
    # but so be it, we'll stick with Click's defaults.)
    assert result.exit_code == 2

    # invalid
    result = runner.invoke(cli.main, input="Foo bar foo baz", args=['-j', 'invalid'])
    assert result.exit_code == 2
    result = runner.invoke(cli.main, input="Foo bar foo baz", args=['-t', 'invalid'])
    assert result.exit_code == 2

    result = runner.invoke(cli.main, input="Foo bar foo baz", args=['-t', 'invalid', '-j', 'invalid', '-s', 'invalid'])
    assert result.exit_code == 2


def test_cli_help(runner):
    """ Smoketest the CLI, for example --help
    """
    help_result = runner.invoke(cli.main, ['--help'], catch_exceptions=False)
    assert help_result.exit_code == 0
    assert '--help' in help_result.output
