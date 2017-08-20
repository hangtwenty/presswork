# -*- coding: utf-8 -*-
""" Command-line interface for presswork. Piping is encouraged. """
import codecs
import sys

import click

from presswork.logging import setup_logging

@click.command()
@click.option('-s', '--strategy',
              # type=click.Choice(['pymc', 'crude']), # TODO add pymc
              type=click.Choice(['crude']),
              help="'pymc' is PyMarkovChain (forked). 'crude' is... crude!",
              default="crude")
@click.option('-i', '--input-text',
              help="defaults to stdin input; you can also specify a valid filepath to read from.",
              default='-')
@click.option('-e', '--input-encoding',
              help="encoding of the input text.",
              default='utf-8')
@click.option('-E', '--output-encoding',
              help="encoding of the output text.",
              default='utf-8')
def main(strategy, input_text, input_encoding, output_encoding):

    setup_logging()

    if input_text == '-':
        UTF8Reader = codecs.getreader(input_encoding)
        sys.stdin = UTF8Reader(sys.stdin)
        input_text = sys.stdin.read()
    else:
        with codecs.open(input_text, 'r', encoding=input_encoding) as f:
            input_text = f.read()

    if strategy == 'crude':
        # TODO refactor such that this is behind a TextMaker class
        from presswork.text_maker._crude import markov_chain_of_sentences_and_words, make_text
        result = make_text(model=markov_chain_of_sentences_and_words(source_text=input_text))
    else:
        raise ValueError('unknown strategy')

    # TODO add pymc
    # elif strategy == "pymc":
    #     from presswork.text_maker.text_maker import TextMakerPyMarkovChain
    #     text_maker = TextMakerPyMarkovChain()

    UTF8Writer = codecs.getwriter(output_encoding)
    sys.stdout = UTF8Writer(sys.stdout)

    sys.stdout.write(result)
    sys.stdout.write("\n")


if __name__ == "__main__":

    main()
