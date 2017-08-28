""" grammar in general: lexical and structural rules. grammar in `presswork`: rules for tokenizing and re-joining.

    >>> word_tokenizer = tokenizers.WordTokenizerWhitespace()
    >>> list(word_tokenizer.tokenize(u'foo bar baz'))
    [u'foo', u'bar', u'baz']
    >>> sentence_tokenizer = tokenizers.SentenceTokenizerNLTK()
    >>> sentence_tokenizer.tokenize(u'Foo bar baz. Another sentence in the input.')
    SentencesAsWordLists([[u'Foo', u'bar', u'baz', u'.'], [u'Another', u'sentence', u'in', u'the', u'input', u'.']])
    >>> sentence_tokenizer = tokenizers.SentenceTokenizerNLTK(word_tokenizer=word_tokenizer)
    >>> sentences = sentence_tokenizer.tokenize(u'Foo bar baz. Another sentence in the input.')
    >>> sentences
    SentencesAsWordLists([[u'Foo', u'bar', u'baz.'], [u'Another', u'sentence', u'in', u'the', u'input.']])
    >>> print joiners.JoinerNLTK().join(sentences)
    Foo bar baz. Another sentence in the input.
    >>> sentences.unwrap()
    [[u'Foo', u'bar', u'baz.'], [u'Another', u'sentence', u'in', u'the', u'input.']]
    >>> print joiners.JoinerWhitespace().join([[u"Duck", u"typed"]])
    Duck typed

---------------------------------------------------------------------------------------
design notes -- Overview of `grammar` child modules; compare/contrast to similar libs
=======================================================================================

    * most common flow for text generators I've played with: text => structured model (=> generate) => rejoin to text
    * more concretely: text => tokenize to sentences (& token sentences to words) (=> generate) => rejoin to text
    * essential data structure is list-of-words: a sentence is just a list-of-words.
    * this is similar to NLTK's view of things, and Markovify's view of things. with some differences:
        * the main diff. vs. Markovify: Markovify uses the Sentences-As-Word-Lists structure too,
            but then stringifies a bit eagerly (i.e. before returning anything, if you want to post-process
            you have to redundantly tokenize, and that can be lossy, messy).
        * not "different" from NLTK, just much narrower: NLTK is the toolkit, this is one narrow application.
            for this version we don't need parse trees etc, just that structure of sentences, is enough
    * keep Tokenizer step separate from Joiner step; defer joing-back-to-text as long as possible. Then
        the Joiner strategies can be pluggable. Later we can eventually process (map(), filter()...) the
        sentences/ word lists, while still structured ... so that's another reason to keep joining 'lazy'

-------------------------------------------------------------------------------
design notes -- WordTokenizers, SentenceTokenizers
===============================================================================

    * These are collaborators: Each SentenceTokenizer has its own default WordTokenizer, but can be customized.
    * SentenceTokenizer takes in one string, tokenizes to sentences, then calls a WordTokenizer on each sentence
    * WordTokenizer takes in a list of strings (sentence-strings) and tokenizes each. (to 'words'.)
    #... see `tokenizers` module for more info

-------------------------------------------------------------------------------
design notes -- WordList, SentencesAsWordLists
===============================================================================

    * simple containers, plus sanity checks.
        * [ [word, word, ...], [word, word, ...], ... ]
    #... see `containers` module for more info

-------------------------------------------------------------------------------
design notes -- Joiners
===============================================================================

    * a Joiner takes in SentencesAsWordLists and joins the tokens back into strings according to some strategy.
    #... see `joiners` module for more info

"""

from . import containers   # NOQA
from . import joiners   # NOQA
from . import tokenizers   # NOQA
