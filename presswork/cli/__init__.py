# -*- coding: utf-8 -*-
""" Command-line interface for presswork. Piping is encouraged. """
import codecs
import sys

import click

from presswork import constants
from presswork.log import setup_logging
from presswork.sanitize import SanitizedString
from presswork.text import grammar
from presswork.text import text_makers


@click.command()
@click.option('-i', '--input-filename',
              help="what to read to train the markov chain. default expectation: you will pipe things in on stdin. "
                   "if you do not use stdin, give this param with a filename to read from.",
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
              type=click.Choice(['markovify', 'pymc', 'crude']),
              help="which strategy to use for markov chain model & text generation. "
                   "'markovify' is a good default choice. "
                   "'pymc' is based on PyMarkovChain. "
                   "'crude' is crude and limited. ",
              default="markovify")
@click.option('-t', '--tokenize-strategy',
              type=click.Choice(['nltk', 'just_whitespace']),
              help="which strategy to use for tokenizing the input text before training the model. "
                   "'nltk' uses NLTK's recommended sentence & word tokenizers (Punkt & Treebank). "
                   "'just_whitespace' will consider sentences to be line separated, and words whitespace separated. ",
              default='nltk')
@click.option('-e', '--input-encoding', help="encoding of the input text.", default='utf-8', show_default=True)
@click.option('-E', '--output-encoding', help="encoding of the output text.", default='utf-8', show_default=True)
def main(ngram_size, strategy, tokenize_strategy, input_filename, input_encoding, output_encoding, count,):
    logger = setup_logging()
    logger.debug("CLI invocation variable dump: {}".format(locals()))

    if input_filename == '-':
        UTF8Reader = codecs.getreader(input_encoding)
        sys.stdin = UTF8Reader(sys.stdin)
        input_text = sys.stdin.read()
    else:
        with codecs.open(input_filename, 'r', encoding=input_encoding) as f:
            input_text = f.read()

    logger.debug("CLI invocation variable dump again: {}".format(locals()))
    text_maker = text_makers.create_text_maker(
            strategy=strategy,
            sentence_tokenizer=tokenize_strategy,
            input_text=SanitizedString(input_text),
            ngram_size=ngram_size)

    # TODO here, we should either not "know" about sentences & joining, or it should be selectable as CLI arg
    sentences = text_maker.make_sentences(count)
    result = grammar.rejoin(sentences)

    UTF8Writer = codecs.getwriter(output_encoding)
    sys.stdout = UTF8Writer(sys.stdout)

    sys.stdout.write(result)
    sys.stdout.write("\n")


if __name__ == "__main__":   # pragma: no cover
    main()
