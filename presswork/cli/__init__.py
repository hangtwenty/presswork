# -*- coding: utf-8 -*-
""" Command-line interface for presswork. Piping is encouraged. """
import codecs
import sys

import click

from presswork import constants
from presswork.log import setup_logging
from presswork.sanitize import SanitizedString
from presswork.text import text_makers


@click.command()
@click.option('-i', '--input-text',
              help="input text to train the markov chain. by default it is expected you will pipe things in on stdin. "
                   "if you do not use stdin, you can specify a valid filepath to read from.",
              default='-')
@click.option('-c', '--count',
              type=int,
              help="count of sentences to generate.",
              default=100,
              show_default=True)
@click.option('-n', '--ngram-size',
              type=int,
              help="how many tokens per n-gram in the model. AKA 'state size' or 'window size'. "
                   "for details, see README, docstrings in code, etc.)",
              default=constants.DEFAULT_NGRAM_SIZE,
              show_default=True)
@click.option('-s', '--strategy',
              type=click.Choice(['pymc', 'crude']),
              help="which implementation/strategy to use for markov chain text generation. "
                   "'markovify' is the most performant and best for most purposes. "
                   "'pymc' is based on PyMarkovChain. "
                   "'crude' is crude and limited. ",
              default="crude")
@click.option('-e', '--input-encoding', help="encoding of the input text.", default='utf-8', show_default=True)
@click.option('-E', '--output-encoding', help="encoding of the output text.", default='utf-8', show_default=True)
def main(strategy, ngram_size, input_text, count, input_encoding, output_encoding):
    logger = setup_logging()

    if input_text == '-':
        UTF8Reader = codecs.getreader(input_encoding)
        sys.stdin = UTF8Reader(sys.stdin)
        input_text = sys.stdin.read()
    else:
        with codecs.open(input_text, 'r', encoding=input_encoding) as f:
            input_text = f.read()

    text_maker = text_makers.create_text_maker(
            input_text=SanitizedString(input_text),
            strategy=strategy,
            ngram_size=ngram_size)

    # TODO over here we shouldn't know about sentences and joining. when text maker has a make_text method, switch to that
    sentences = text_maker.make_sentences(count)
    logger.debug('sentences=' + str(sentences))
    result = text_makers.rejoin(sentences)

    UTF8Writer = codecs.getwriter(output_encoding)
    sys.stdout = UTF8Writer(sys.stdout)

    sys.stdout.write(result)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
