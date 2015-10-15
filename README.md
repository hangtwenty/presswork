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

To install, grab the github repository. (Not utilitarian/clean so I'm not putting it on PyPI)

background
==========

* Forked from [TehMillhouse/PyMarkovChain](https://github.com/TehMillhouse/PyMarkovChain)
* Purpose: generate text for a blog poking fun at reviews of electronic music,
which are often very ... inspired? Whimsical? Off-the-wall? I only wrote a few,
but check them out (warning, contains graphic content): [Presswork](http://presswork.tumblr.com/)
