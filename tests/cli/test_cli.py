#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `presswork` package."""

import pytest

from click.testing import CliRunner

from presswork import cli


def test_cli_default_strategy():
    runner = CliRunner()
    result = runner.invoke(cli.main, input="Foo is better than bar. Bar is better than foo")
    assert result.exit_code == 0
    assert 'better than' in result.output


def test_cli_invalid_strategy():
    runner = CliRunner()
    result = runner.invoke(cli.main, input="Foo bar foo baz", args=['--strategy', 'invalid'])
    assert result.exit_code == 2


def test_cli_help():
    """ Smoketest the CLI - with no arguments it should have exit code of 0 (failure). Also test --help.
    """

    runner = CliRunner()

    # with no stdin input and no args, it hangs. click CliRunner returns this as '-1'
    result = runner.invoke(cli.main)
    assert result.exit_code == -1

    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help' in help_result.output
