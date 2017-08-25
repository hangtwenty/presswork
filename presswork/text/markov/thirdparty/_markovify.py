""" adapters for the Markovify lib. consider this class private, and instead use TextMaker interface!
"""
import markovify

from presswork import constants


class Disabled(ValueError):
    """ markovify adapter disables some features to avoid confusion and keep things tight across `presswork`
    """


class NotYetImplementedInAdapter(NotImplementedError):
    """ markovify adapter isn't yet ready to handle these features (need some careful work to integrate)
    """


class MarkovifyLite(markovify.Text):
    """ modifies markovify.Text behavior (using public API). mainly disabling some 'eager' behaviors.

    main thing to adapt is that it 'eagerly' stringifies, whereas we want to keep results as sentences & words
    (lists-of-lists) until later, lazy re-joining. (for max composition flexibility.)
    """

    # noinspection PyMissingConstructor
    def __init__(self, input_text=None, state_size=constants.DEFAULT_NGRAM_SIZE, chain=None, parsed_sentences=None):
        """
        :param input_text: DISABLED, do not pass this. instead, pass parsed_sentences.
        :param ngram_size: the N in N-gram, AKA state size or window size, same as elsewhere
        :param chain:  A trained markovify.Chain instance for this text, if pre-processed.
        :param parsed_sentences:  A list of lists i.e. [ [word, word, ...], [word, word, ...], ... ]
            Assumption - these should be sentence-tokenized & word-tokenized before passing to here.
            in text_makers module there will be a wrapper that does just that.
        """
        # XXX not calling super(); markovify.Text constructor does some things we don't want to do.
        # Overriding, satisfying same needs, but adapting to our purposes

        if input_text:
            raise Disabled(
                    "disabled in this adapter; tokenize beforehand, pass to `parsed_sentences` in constructor")

        self.state_size = state_size
        self.parsed_sentences = parsed_sentences

        self.chain = chain or markovify.Chain(self.parsed_sentences, state_size)

        # The "rejoined_text" variable is checked in make_sentences -> test_sentence_output, which
        # "assesses the novelty of sentences". This is a very cool feature, but so far it depends on the
        # 'eager' stringification that we are trying to get away from. For now, we'll disable it.
        self.rejoined_text = u'<DISABLED>'

    def sentence_join(self, sentences):
        """ Disable markovify's eager re-joining: make this method a no-op. (word_join is part of its public API)

        :param words: list of lists of words
        :rtype: list
        """
        return sentences

    def word_join(self, words):
        """ Disable markovify's eager re-joining, by making this method a no-op.

        this is a bit of abuse since it changes the return type from string to list. however,
        word_join is part of its public API, and we aren't given the option of composition - can only override.

        :param words: list of words
        :rtype: list
        """
        return words

    def generate_corpus(self, text):
        raise Disabled("disabled in this adapter; tokenize beforehand, pass to `parsed_sentences` in constructor")

    def make_sentence(self, init_state=None, **kwargs):
        kwargs['test_output'] = kwargs.get('test_output', False)
        return super(MarkovifyLite, self).make_sentence(init_state, **kwargs)

    def test_sentence_output(self, *args):
        """ used by 'assessing the noevelty of generated sentences', very cool feature, but disabled for now
        """
        # this code should be unreachable unless somebody really tries (since test_output=False in make_sentence)
        raise NotYetImplementedInAdapter("not yet implemented in presswork adapter around markovify")
