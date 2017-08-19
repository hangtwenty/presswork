presswork
=============

This project was just for fun. It provides an easy-to-use text generator using Markov chains. You give it a bunch of text, it generates more text based on those models. It can be used from code, or you can locally run the [Flask](http://flask.pocoo.org) app and rapidly play around through your web browser. It is not utilitarian nor ready for any production purpose... but it was fun! For a library that is more recently maintained, see [jsvine/markovify](https://github.com/jsvine/markovify).

Goal was ease of use. Here's some easy usage from code:

    >>> from presswork import MarkovChainTextMaker
    >>> text_maker = MarkovChainTextMaker("/tmp/markov")
    >>> text_maker.database_init("Beautiful is better than ugly. Explicit is better than implicit.")
    >>> print text_maker.make_sentences(2)
    Explicit is better than ugly .  Beautiful is better than implicit .

The local [Flask](http://flask.pocoo.org) app is better though. More details on both, below.

background
==========

* Purpose: generate some text - specifically I wanted to write some parodies of music reviews, specifically of some electronic and experimental music I love. I love the music, but the reviews can be a bit... funny. So I wanted to poke more fun. I published a couple of posts, and hand some laughs with friends. Here: [Presswerk](http://presswerk.tumblr.com/). I was going to do more, but I turned my attention back to making new music.
* Originally was forked from [TehMillhouse/PyMarkovChain](https://github.com/TehMillhouse/PyMarkovChain)
    * Added sentence tokenization support (via NLTK)
    * Added unit tests (86% test coverage of `presswork` module for now)
    * Added little Flask web app for playing around rapidly

setup
=====

To install and use,

* Grab this GitHub repository. (I feel this code is not utilitarian enough to put it on PyPI)
  `cd` into the directory.
* `pip install -e .` to install `presswork` (in a [virtualenv](https://virtualenv.pypa.io/en/latest/))
* Install dependencies.
    * `pip install -r requirements.txt`
    * If you plan to use the [Flask](http://flask.pocoo.org) web app, you need to also do `pip install -r requirements_server.txt`
* Download required [NLTK](http://www.nltk.org/) corpora. There's a script in here to help: `python ./scripts/download_corpora.py`


recommended usage: play with the web app locally
===============

My preferred way to use this is to keep generating text, selectively grabbing the bits I like and copying out to a notepad... sometimes feeding things back in, sometimes adding in new source texts... but always sort of "collaging" between the source text, generated text, and so on. Entertaining results, regardless.

Running the Flask app locally is easy.

    # ASSUMPTION: you have already done `pip install -r requirements-server.txt`
    $ python flask_app/app.py 8080
                             #^^^^ pick any port you want. defaults to Flask's default (5000)

Then in your web browser, go to http://localhost:8080, or whatever port, and play around. Here is a snapshot from [when I was jamming with reviews of Oneohtrix Point Never](http://presswerk.tumblr.com/).

![Input to presswork web app](.readme_images/presswork_web_app_input.png)
![Output from presswork web app](.readme_images/presswork_web_app_output.png)



#### Caveats

* Suitable only for local usage, **please** don't deploy it anywhere.
* As currently written, I don't have the Markov database/corpora persisting between runs/submissions. That is, each time you submit text, it loads in, and generates and outputs; next submission is a clean slate. This was the maximum flexibility for a first cut, and it was the workflow I wanted. To include various source texts at once, just paste all in the input box (and to save that input for multiple rounds of generation, just select-all and copy, re-inputting as needed). If you want to "accumulate" text as you go, go ahead: continue feeding the output back into the input. Or combine output with other freshi nputs. YMMV but this was was exactly the kind of workflow as I was after for this frivolous purpose :-)
* I haven't optimized the performance. Large input takes longer to handle, so if you throw in whole books from Project Gutenberg it will hang a bit

#### A similar workflow, that would get around the caveats

To get around those caveats without addressing directly, switch to scripting and a text editor. Make a script - follow the usage examples seen in `flask_app` module, using `presswork` module. Have your script read from a file repeatedly. Edit that file in your favorite plaintext editor, frequently saving, maybe retriggering your script upon each save (many ways to do that). Less instant gratification to set up, but bit snappier and less messy, if for some reason you want to get serious about making silly text ;-)

### More code details

For more usage examples see `flask_app` as well as `tests/test_presswork.py`. Also, the code is pretty self-explanatory and has docstrings too.

Note about storage/'database' - presswork persists the Markov model using `pickle` (you can choose what path). Its data structure is a dictionary of probabilities/scores, and functions. This entails that you have to use the same version of python to store the data and to restore the data - `pickle` changed between Python 2 and 3.

### Test coverage snapshot

```
$ py.test --cov presswork
======================================= test session starts ========================================
platform darwin -- Python 2.7.10, pytest-3.0.1, py-1.4.31, pluggy-0.3.1
rootdir: /Users/mfloering/Workspace/presswork, inifile:
plugins: cov-2.3.1
collected 3 items

tests/test_presswork.py ...

---------- coverage: platform darwin, python 2.7.10-final-0 ----------
Name                     Stmts   Miss  Cover
--------------------------------------------
presswork/__init__.py        1      0   100%
presswork/presswork.py     131     18    86%
--------------------------------------------
TOTAL                      132     18    86%
```

what I would improve if I pick this back up
============

This library is rudimentary and just for fun. If I pick it back up to play with it more, these are the changes I would make.

* Main code - PROBABLY swap out the default Markov implementation with using more robust implementation from [markovify](https://github.com/jsvine/markovify library)
    * Then wire up configurability improvements as noted below
    * CAVEAT: it seems that markovify lib is using its own quick splitters/tokenizers. Maybe I would fork it, and add the option to use NLTK as backend (make pluggable)
* Morevoer, the Markov implementation should be pluggable. Then I could swap with others like https://github.com/pteichman/cobe and see what's best.
* Main code - regardless of which Markov implementation (stick with current one or switch to markovify), I wanted to make these chanes:
    * Configurable support for different tokenizers from NLTK. (Word tokenizer could be swapped out, sentence tokenizer could also be swapped out. Dropdown in the Flask app could be good.)
    * Make the *stopwords* setup configurable, at code level and maybe Flask app too.
    * Configurable support for handling contractions (i.e. option to replace "don't" with "do not"
    in case that makes for better text generation with your input corpus)
    * Improve punctuation handling. It's handling puncutation in a silly way. I have some logic to ensure `"foo"` and `"foo."` are treated as separate tokens, but it's handled crudely (just a first cut). So currently when the tokens are joined together into a string and returned to user, there is whitespace around all the punctuation, which forces some manual editing before finally using the generated text. Fixing this up won't be hard, just have to do it.
* Web application
    * Add options to the Flask app for persisting the database between runs, but also freely clearing it, switching between database files, and so on
        * Pick any filepath
        * Select/autocomplete from filepaths used so far (enable workflow of easily switching between modes/presets)
        * Clear database file (back up to /tmp/ then clear)
    * There are already tests for the `presswork` module but none for the Flask app. Could add some.

development
===========

* Run tests with pytest (`py.test` in this directory).
* Run tests of supported Python versions, from clean slate, with tox (`tox` in this directory).
