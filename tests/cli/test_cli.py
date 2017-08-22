#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests for presswork CLI
"""
from mock import patch
import pytest

from click.testing import CliRunner

from presswork import cli


@pytest.fixture
def runner():
    return CliRunner()

def test_cli_larger_input_from_file(runner, filename_newlines):
    result = runner.invoke(cli.main, args=['--input-text', ], catch_exceptions=False)
    # TODO have this do some kind of sanity check of contents... i.e. tokens in output are subset of tokens in input?
    assert result.output.strip()

def test_cli_larger_input_from_stdin(runner, text_newlines):
    result = runner.invoke(cli.main, input=text_newlines, args=['--input-text', '-'], catch_exceptions=False)
    # TODO have this do some kind of sanity check of contents... i.e. tokens in output are subset of tokens in input?
    assert result.output.strip()


def test_cli_default_strategy(runner):
    """ tests the ease-of-use requirement for the CLI, that with no --strategy arg, some default MC behavior happens.
    """
    result = runner.invoke(cli.main, input="Foo is better than bar. Foo is better than baz.", catch_exceptions=False)
    assert result.exit_code == 0
    assert 'better than' in result.output


def test_cli_choose_strategy_crude(runner):
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
        result = runner.invoke(cli.main, input=stdin, args=["--strategy", "unknown"], catch_exceptions=True)
        assert not mock.called

    # # TODO when I add markovify strategy, enable this
    # # another positive case
    # with patch(target="presswork.text.text_makers.TextMakerMarkovify.input_text") as mock:
    #     result = runner.invoke(cli.main, input=stdin, args=["--strategy", "markovify"], catch_exceptions=False)
    #     assert result.exit_code == 0
    #     assert mock.called

@pytest.mark.parametrize("stdin", [
    "",
    " ",
    "  ",
    "\n",
    "\r",
    "\n\r",
    "\x20",
    # TODO also have tests for null byte in test_parity etc., cos this totally broke things! should close closer to the unit level too.
    "\x00",
])
def test_cli_empty_inputs(runner, stdin):
    """ had a regression during development where for `crude` empty inputs were causing undefined behavior.

    that should be tested closer to the unit that is at fault (tests for `crude`), but should be tested here too,
    as the CLI shouldn't panic or wait on an infinite loop in these cases. (regardless of impl details)
    :param runner:
    :return:
    """

    # it'll hang if stdin is empty (haven't figure out exactly how to test that, but it doesn't seem crucial).
    # but more definitely, if you do 'echo | presswork', it should return exit code 0 and no output.
    result = runner.invoke(cli.main, input=stdin, catch_exceptions=False, args=['--strategy', 'crude'])
    assert result.exit_code == 0
    assert result.output.strip() == ''


def test_cli_invalid_strategy(runner):
    result = runner.invoke(cli.main, input="Foo bar foo baz", args=['--strategy', 'invalid'])
    # (side note, it is odd that Click library uses 2 for invalid choices (http://tldp.org/LDP/abs/html/exitcodes.html)
    # but so be it, we'll stick with Click's defaults.)
    assert result.exit_code == 2


def test_cli_help(runner):
    """ Smoketest the CLI, for example --help
    """
    help_result = runner.invoke(cli.main, ['--help'], catch_exceptions=False)
    assert help_result.exit_code == 0
    assert '--help' in help_result.output
