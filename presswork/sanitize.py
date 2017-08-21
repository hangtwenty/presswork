""" common sanitization functions, should be used *at least* before loading source text.
"""
import re

control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
control_char_re = re.compile('[%s]' % re.escape(control_chars))

def remove_control_characters(string_or_unicode):
    """ remove control characters regardless of whether they are ASCII or unicode

    solution is from here, https://stackoverflow.com/a/93029/884640
    ... surprised there is no stdlib function for it, but this will do.

    some redundancy in this test but just to be thorough as well as obvious...
    ... it does repeat the definition of control_chars basically for example, but that is intentional

        >>> import random, sys
        >>> null_byte = chr(0)
        >>> basic_input = "hello" + null_byte + "world"
        >>> assert null_byte in basic_input
        >>> assert null_byte not in remove_control_characters(basic_input)
        >>> all_chars = (unichr(i) for i in xrange(sys.maxunicode))
        >>> all_chars_as_list = list(all_chars)
        >>> random.shuffle(all_chars_as_list)
        >>> all_chars_shuffled = "".join(all_chars_as_list)
        >>> del all_chars, all_chars_as_list
        >>> all_chars_except_control_chars = remove_control_characters(all_chars_shuffled)
        >>> assert null_byte not in all_chars_except_control_chars
        >>> control_char_nums = range(0, 32) + range(127, 160)
        >>> for character in map(unichr, control_char_nums):
        ...     assert character not in all_chars_except_control_chars

    :param string_or_unicode:
    :return:
    """
    return control_char_re.sub('', string_or_unicode)


if __name__ == "__main__":
    import pdb; pdb.set_trace()