presswork
=============

Presswork supplies an easy-to-use implementation of a Markov chain text generator.
It is intended (and slightly tweaked) to help you have fun with journalistic writing.

Note, it is not optimized for outputting well-formatted text without human intervention.
It leaves spaces around punctuation for example, assuming you'll come back and edit
the text before doing something with it.

PyMarkovChain supplies an easy-to-use implementation of a markov chain text generator.  
To use it, you can simply do

    #!/usr/bin/env python

    from presswork import presswork
    # Create an instance of the markov chain. By default, it uses MarkovChain.py's location to
    # store and load its database files to. You probably want to give it another location, like so:
    mc = MarkovChainTextMaker("/tmp/markov")
    # To generate the markov chain's language model ...
    mc.generateDatabase("This is a string of Text. It won't generate an interesting database though.")
    # To let the markov chain generate some text, execute
    mc.generateString()

presswork persists the Markov model using pickle, dumping a dictionary.
(A tree structure of probabilities and functions, that can easily be reloaded/unpickled 
to train the model on more data, later).

This entails that you have to use the same version of python to store the data and to
restore the data, as pickle is one of those things that have changed from python2 to python3.

setup
=====

To install and use,

    * Grab the GitHub repository. (I feel this code is not utilitarian enough to put it on PyPI)
      `cd` into the directory.
    * Run script to download required [NLTK](http://www.nltk.org/) corpora: `python ./scripts/download_corpora.py`
    * Install `presswork`: `pip install .`
    * Use from code or via thin web application:
        * From code: `import presswork` and do your thing - see usage example above
        * Web application: `python server/app.py` or for another port like 8080, `python server/app.py 8080`

web application
===============

Notes:

* Suitable only for local usage, don't deploy it anywhere.
* As currently written, it doesn't use a database, so each text submission is a clean slate.
If you want to "accumulate" text just paste more in the textarea.


room for improvement!
============

This library is rudimentary and just for fun. But already I think these things would be nice,
maybe I will do them:

* Main code
    * Format punctuation better so there isn't extra whitespace around every punctuation mark
    * Configurable support for *stopwords*
    * Configurable support for handling contractions (i.e. option to replace "don't" with "do not"
    in case that makes for better text generation with your input corpus)
* Web application
    * Add options for using a database (well)
        * Pick filepath
        * Clear database file
        * Switch between persistent database files

background
==========

* Forked from [TehMillhouse/PyMarkovChain](https://github.com/TehMillhouse/PyMarkovChain)
* Purpose: generate text for a blog poking fun at reviews of electronic music,
which are often very ... inspired? Whimsical? Off-the-wall? I only wrote a few,
but check them out (warning, contains graphic content): [Presswork](http://presswork.tumblr.com/)
