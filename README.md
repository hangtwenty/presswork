[![Build Status](https://travis-ci.org/hangtwenty/presswork.svg?branch=master)](https://travis-ci.org/hangtwenty/presswork) 
[![Code Climate](https://codeclimate.com/github/hangtwenty/presswork/badges/gpa.svg)](https://codeclimate.com/github/hangtwenty/presswork) [![Test Coverage](https://codeclimate.com/github/hangtwenty/presswork/badges/coverage.svg)](https://codeclimate.com/github/hangtwenty/presswork/coverage)


## presswork

A workbench for generative text!

So far, it's all about [Markov](https://blog.codinghorror.com/markov-and-you/)
[Chains](https://en.wikipedia.org/wiki/Markov_chain). [Here's a great visual explanation of Markov Chains.](http://setosa.io/blog/2014/07/26/markov-chains/index.html) Given a bunch of text, model it, and generate "probable" new sentences.

Currently offers:

* **CLI** for piping in found text, piping out generated text (could be used with other tools)
* **Flask app** for jamming with text (for local usage)
* **Python toolkit**
    * The text generation tools, broken down for mix and match (composite reuse)

I'd like to add other tools to the toolkit, building off of this foundation.

## Why

Started for fun: I wanted to generate/write some [parodies of music reviews about experimental music](http://presswerk.tumblr.com/).
(Poking fun at something I love.)

I picked it back up to explore the "creative text generation" domain a bit more. 
I separated some concerns, and experimented with different strategies for each concern.

### Example of mixing and matching

Here's mixing and matching with the CLI. (It outputs a lot more than this, these are just some snippets of output.)

    $ presswork --input-filename *.txt
    I feel lucky to have evolved flight and others have not. If history is any guide, we copied their interview process ...

    $ presswork --join just_whitespace < cat ~/found_texts/*
    An erroneous manual operation
    Consequently the attempt to break the physical laws

    $ presswork --join random_enjamb -i *.txt
    The answer
        is complicated,
              and timidly said
    That
            ye may eat the flesh
                    of all reality.

    But we live in an artificial intelligence.
            How could you live so blind
            to your surroundings?

You may fiddle with the Markov Chain strategy, tokenizer strategy, and joiner strategy. Another important parameter
is the [N-gram size](https://en.wikipedia.org/wiki/N-gram) (how "tightly" to model the input text).

For example

    $ presswork --strategy pymc --tokenize nltk --join random_indent --ngram-size 3 --input-encoding raw < *.txt

    # or another example with short arguments
    $ presswork -s markovify -t just_whitespace -j nltk -n 3 -e utf-8 -i senate-bills.txt

To find out more:

    $ presswork --help

You can access the same options to mix and match, when using the local Flask app.
CLI and Flask app both have help at hand, and you can explore the code and docs for deeper detail.

### Looking forward

I want to explore the "creative text generation" domain more. This pet project is just a start :-)

What about...

* other text generators?
    * "modified Markov" where a model is edited by hand or series of interactive prompts, then put back in
    * abuse TensorFlow one way or another
* other joiners?
    * instead of just indenting somewhat randomly, what if there were joiners that were context-aware,
following some more structured rules?
* we avoid joining back to text until final display. while the data is still structured (as sentences and words),
what else could we "pipe" it through?
    * various ways to `map()` and `filter()` the stream of generated sentences and words
    * various ways to swap out some words words before output. For example, use NLTK WordNet to find synonyms, 
        and choose rhyming words


### This is undercooked! See also...

This is undercooked! It's not on PyPI because you should only use it if you're cloning it, and getting your hands dirty.
(If you end up enjoying it, or extending it, please get in touch! File issues! Etc! Cheers.)

For a great Markov Chain text generation **library**,
 use [`markovify`](https://github.com/jsvine/markovify). (`markovify` is used in the default text generation strategy here.)

----

## How

Workflow note: it's tough to create the perfect recipe of inputs, to get great unedited outputs every time. What I do: generate a lot, skim-read, and copy out my favorite parts to another buffer. Repeat. Revise.

### Flask app usage

Running the Flask app locally is easy.

    $ python flask_app/app.py 5000
                                 # pick any port. defaults to Flask's default (5000)

    # or to run in Flask's wonderful debug mode, just set "DEBUG" variable
    $ DEBUG=1 python flask_app/app.py

Then in your web browser, go to http://localhost:5000, or whatever port, and play around.

**Do not deploy this anywhere.** Thank you :-)

### CLI usage

Reads from files or stdin, accepts a few params.

    $ presswork --help

For best results, use a nice terminal with easy copy and paste right when you highlight text (I like iTerm2).

### Python usage

The short of it:

* Everything has sane/ "preferred" defaults
* But it mostly uses Composite Reuse to let you customize, mix and match

There are loads of docstrings and doc tests, which demonstrate usage of more parts. Here is a quick rundown.

    >>> from presswork.text_makers import create_text_maker
    >>> text_maker = create_text_maker(input_text=text, ngram_size=3)
    >>> text_maker.make_sentences(100)
    #...

    >>> text_maker = create_text_maker(strategy="pymc", sentence_tokenizer="nltk", joiner="random_indent")
    >>> text_maker.join(text_maker.make_sentences(100))
    #...

    >>> from presswork.text.grammar import SentenceTokenizerNLTK, WordTokenizerWhitespace
    >>> from presswork.text_makers import TextMakerPyMarkovChain
    >>> custom_tokenizer = SentenceTokenizerPyMarkovChain(word_tokenizer=WordTokenizerWhitespace())
    >>> tm = TextMakerCrude(sentence_tokenizer=custom_tokenizer)
    >>> tm.input_text("This text was input to a customized text maker")
    >>> tm.join(tm.make_sentences(1)))
    u'This text was input to a customized text maker'

    >>> tm = create_tm(strategy="markovify")
    >>> tm.input_text(...)


### Setup

1. Grab this repo (withheld from PyPI for now, because it is not utilitarian)
2. [virtualenv](https://virtualenv.pypa.io/en/latest/)
3. Install
    - **quick:** **`make install`**. This will do `pip install`, then also install NLTK corpora dependencies.
    - or **custom:**
        1. `pip install .` to install `presswork` plus dependencies. (or `pip install -e .` for editable/development mode.)
        2. Download required [NLTK](http://www.nltk.org/) corpora.
            * `python setup.py install_with_nltk_corpora`
            * NLTK allows you to change the corpora directory by setting `NLTK_DATA` (defaults are fine for most users though)


----------------

## Test coverage snapshot

One of the best things this has going for it -- thorough tests, and good coverage.

```
Name                                                 Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------
presswork/__init__.py                                    0      0   100%
presswork/__main__.py                                    0      0   100%
presswork/cli/__init__.py                               41      0   100%
presswork/cli/__main__.py                                0      0   100%
presswork/constants.py                                   1      0   100%
presswork/flask_app/__init__.py                          0      0   100%
presswork/flask_app/app.py                              54      2    96%   82-83
presswork/log/__init__.py                               17      0   100%
presswork/text/__init__.py                               0      0   100%
presswork/text/clean.py                                 49      1    98%   79
presswork/text/grammar/__init__.py                       3      0   100%
presswork/text/grammar/containers.py                    31      0   100%
presswork/text/grammar/joiners.py                       72      1    99%   107
presswork/text/grammar/tokenizers.py                    72      4    94%   42, 45, 70, 87
presswork/text/markov/__init__.py                        0      0   100%
presswork/text/markov/_crude_markov.py                  73      6    92%   63-64, 73-76
presswork/text/markov/thirdparty/__init__.py             0      0   100%
presswork/text/markov/thirdparty/_markovify.py          23      0   100%
presswork/text/markov/thirdparty/_pymarkovchain.py     100      1    99%   168
presswork/text/text_makers.py                          130      2    98%   135, 166
presswork/utils.py                                       9      0   100%
----------------------------------------------------------------------------------
TOTAL                                                  675     17    97%
#...
=================== 1137 passed, 4 warnings in 497.41 seconds ====================
```

(1137 tests!? Well, they're [parametrized with py.test.](https://docs.pytest.org/en/latest/parametrize.html)
Many combinations of parameters are tested.)

## Miscellaneous

* It's got pretty good support for Unicode and **mixed encodings** too. This is very crucial for found text.
* By default, it leverages NLTK for tokenization and de-tokenization. NLTK is a good default tool for this job.

### More about the Markov Chain strategies

* `crude` is home grown, mainly serving as a reference implementation
* third party
    * [`markovify`](https://github.com/jsvine/markovify)
    * `pymc` - this is a **forked** version of [PyMarkovChain](https://github.com/TehMillhouse/PyMarkovChain),
        mostly kept the same

Markovify and PyMarkovChainFork each have their own pros and cons. They are quite similar, but you can see from
playing with them, how they are different. Markovify is the default.

The `crude` strategy was just an exercise, and is kept as a reference implementation - and something to test the others
against. This one is homegrown and is kept un-optimized - priority for this one is easy-to-understand code, trading
off the other considerations (memory, speed).

For both PyMarkovChainFork and 'crude', there is full unicode support, as well as best-effort support for
mixed encodings. Because we can't be too choosy with found-text! You **can** hit issues with NLTK, but they should
not be common now. Please file an issue if you hit one.

### More about the `tokenizers` and `joiners`

Just try them out ;-) And try adding your own! Pull requests are very welcome.

### Known limitations

* **`markovify` has awesome features we're not exposing yet.** I disabled these at first to reduce scope, but it'd
be nice to get these integrated well.
    * [weighted combination of models](https://github.com/jsvine/markovify#combining-models),
        you can make it so texts don't "win" just by length
    * [automatically filtering sentences to choose novel, new ones](https://github.com/jsvine/markovify/blob/4880754989a7bab272745340a11a2ba165c1216b/markovify/text.py#L116-L122)
* Input & output 'cleaning' both are off to a good start, but need more work. There's definitely "cruft" in the output
* No persistence yet. All 3 Markov Strategies could have the model persist on disk, but they each do it
in a different way. No unified interface for this part, yet
* Natural language is limited to English and English-like languages. (Namely, left-to-right reading.)
    * If using with a language besides English, that's awesome, please file issues as you encounter them. 
    `nltk` can probably support what you want, but surely we have to iron out some kinks here.

### Development & exploration

* Run tests with pytest (`py.test` in this directory).
* Run tests of supported Python versions, from clean slate, with tox (`tox` in this directory). Currently just Python 2.7

----

👁 Happy text generating 👁
