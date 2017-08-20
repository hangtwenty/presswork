#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `presswork` package."""

import pytest

from click.testing import CliRunner

from presswork import cli

@pytest.fixture
def runner():
    return CliRunner()


def test_cli_default_strategy(runner):
    """ tests the ease-of-use requirement for the CLI, that with no --strategy arg, some default MC behavior happens.
    """
    result = runner.invoke(cli.main, input="Foo is better than bar. Bar is better than foo")
    assert result.exit_code == 0
    assert 'better than' in result.output


def test_cli_invalid_strategy(runner):
    result = runner.invoke(cli.main, input="Foo bar foo baz", args=['--strategy', 'invalid'])
    # (side note, it is odd that Click library uses 2 for invalid choices (http://tldp.org/LDP/abs/html/exitcodes.html)
    # but so be it, we'll stick with Click's defaults.)
    assert result.exit_code == 2


def test_cli_help(runner):
    """ Smoketest the CLI, for example --help
    """
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help' in help_result.output

    # it'll hang if stdin is empty (haven't figure out exactly how to test that, but it doesn't seem crucial).
    # but more definitely, if you do 'echo | presswork', it should return exit code 0 and no output.
    result = runner.invoke(cli.main, input='')
    assert result.exit_code == 0
    assert result.output.strip() == ''
