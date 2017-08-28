# -*- coding: utf-8 -*-
""" Command-line interface for presswork. Piping is encouraged. """
import codecs
import sys

import click

from presswork import constants
from presswork.log import setup_logging
from presswork.text import clean
from presswork.text import text_makers
from presswork.text.grammar import joiners
from presswork.text.grammar import tokenizers


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
              type=click.Choice(text_makers.TEXT_MAKER_NICKNAMES),
              help="which strategy to use for markov chain model & text generation. "
                   "'markovify' is a good default choice. "
                   "'pymc' is based on PyMarkovChain. "
                   "'crude' is crude and limited. ",
              default="markovify")
@click.option('-t', '--tokenize',
              type=click.Choice(tokenizers.TOKENIZER_NICKNAMES),
              help="which strategy to use for tokenizing the input text before training the model. "
                   "'nltk' uses NLTK's recommended sentence & word tokenizers (Punkt & Treebank). "
                   "'just_whitespace' will consider sentences to be line separated, and words whitespace separated. "
                   "'markovify' uses both punctuation and whitespace; may be faster than 'nltk', but less precise.",
              default='nltk')
@click.option('-j', '--join',
              type=click.Choice(joiners.JOINER_NICKNAMES),
              help="which strategy to use for joining the text back together, before output. "
                   "'nltk' uses NLTK's recommended de-tokenizer, MosesDetokenizer. "
                   "'random_indent' is like 'nltk' but randomly indents lines. "
                   "'random_enjamb' is like 'random_indent' but also randomly breaks sentences over lines. "
                   "'just_whitespace' just uses newlines and spaces. ",
              default='nltk')
@click.option('-e', '--input-encoding',
              help="encoding of the input text. uses Python's encoding names. one special case - "
                   "if you change to 'raw', it'll try to use Python/shell defaults.",
              default='utf-8',
              show_default=True)
@click.option('-E', '--output-encoding', help="encoding of the output text.", default='utf-8', show_default=True)
def main(ngram_size, strategy, tokenize, join, input_filename, input_encoding, output_encoding, count, ):
    logger = setup_logging()
    logger.debug("CLI invocation variable dump: {}".format(locals()))

    if input_filename == '-':
        if input_encoding == "raw":
            input_text = sys.stdin.read()
        else:
            UTF8Reader = codecs.getreader(input_encoding)
            sys.stdin = UTF8Reader(sys.stdin)
            input_text = sys.stdin.read()
    else:
        if input_encoding == "raw":
            with open(input_filename, 'r') as f:
                input_text = f.read()
        else:
            with codecs.open(input_filename, 'r', encoding=input_encoding) as f:
                input_text = f.read()

    logger.debug("CLI invocation variable dump again: {}".format(locals()))
    text_maker = text_makers.create_text_maker(
            strategy=strategy,
            sentence_tokenizer=tokenize,
            joiner=join,
            input_text=clean.CleanInputString(input_text),
            ngram_size=ngram_size)

    output_sentences = text_maker.make_sentences(count)
    output_text = text_maker.join(output_sentences)
    final_result = text_maker.proofread(output_text)

    UTF8Writer = codecs.getwriter(output_encoding)
    sys.stdout = UTF8Writer(sys.stdout)

    sys.stdout.write(final_result)
    sys.stdout.write("\n")


if __name__ == "__main__":  # pragma: no cover
    main()
