""" utilities to help do comparisons in tests - esp. given that correct behavior here is (usually) not deterministic
"""
import re
import string

from presswork.text import sentences_and_words

re_punctuation = re.compile('[%s]' % re.escape(string.punctuation))


def remove_all_punctuation(s):
    """ efficient removal of ASCII punctuation (just punctuation not whitespace) - from anywhere in strings

    faster than regex in this case actually, more info here: https://stackoverflow.com/a/266162/884640

        >>> assert remove_all_punctuation(string.punctuation) == ""
        >>> assert remove_all_punctuation(string.punctuation + "hello" + string.punctuation) == "hello"
    """
    return re_punctuation.sub('', unicode(s))


def output_text_has_subset_of_words_from_input_text(output_text, input_text):
    """ property of (our) markov-chain-text-generators: will only output 'words' from the input.

    in other words, the possible output-words are a subset of the input-words (more specifically, the words in the
    model that was made from the input text).

        >>> assert output_text_has_subset_of_words_from_input_text("exact", "exact")
        >>> assert output_text_has_subset_of_words_from_input_text("foo bar baz", "foo bar baz foo bar quux foo yah")
        >>> import pytest
        >>> with pytest.raises(ValueError): output_text_has_subset_of_words_from_input_text("...", "...")
    """
    output_words = sentences_and_words.crude_split_words(
            remove_all_punctuation(output_text))
    input_words = sentences_and_words.crude_split_words(
            remove_all_punctuation(input_text))

    # make sure we're not comparing empty sets -set().issubsetof({1,2,3}) == True, but doesn't mean much for us.
    if not output_words or not input_words:
        raise ValueError("this test is not meaningful if either side of comparison is empty, check for other errors")

    return set(output_words).issubset(set(input_words))
