""" SentencesAsWordLists, WordList ... Thin containers for our tokenized text.

-------------------------------------------------------------------------------
design notes -- SentencesAsWordLists, WordList
===============================================================================

    * simple containers, maybe with some helper methods
        * [ [word, word, ...], [word, word, ...], ... ]
    * Keep duck-typing in mind - most things that use these, should also Just Work when given plain lists,
        or plain lists-of-lists. don't type-check strictly, stay compatible with primitives/builtins
    * if helper methods are added to them, they should be just that - HELPERS - i.e. things should work OK
        without them. just 'guardrails' or 'progressive enhancements', if that makes sense.
"""

from UserList import UserList


class SentencesAsWordLists(UserList):
    """ just a list of lists of strings - with Just Enough sanity checking (yet still permitting duck typing)

        >>> import pytest
        >>> with pytest.raises(ValueError): SentencesAsWordLists('wrong_data_structure ... a string')
        >>> with pytest.raises(ValueError): SentencesAsWordLists(['wrong_data_structure', 'flat', 'list'])
        >>> list_of_lists_of_strings = [["ok", "here", "are"], ["lists", "of", "words"]]
        >>> assert SentencesAsWordLists(list_of_lists_of_strings) == list_of_lists_of_strings
        >>> print repr(SentencesAsWordLists(list_of_lists_of_strings))
        SentencesAsWordLists([['ok', 'here', 'are'], ['lists', 'of', 'words']])
        >>> print repr(SentencesAsWordLists(list_of_lists_of_strings).unwrap())
        [['ok', 'here', 'are'], ['lists', 'of', 'words']]
        >>> assert SentencesAsWordLists.ensure(list_of_lists_of_strings) == list_of_lists_of_strings
        >>> print SentencesAsWordLists.ensure(list_of_lists_of_strings).unwrap()
        [['ok', 'here', 'are'], ['lists', 'of', 'words']]
        >>> C = SentencesAsWordLists
        >>> assert C.ensure(C.ensure(C.ensure(C.ensure((list_of_lists_of_strings))))) == list_of_lists_of_strings
    """

    def __init__(self, seq):
        super(SentencesAsWordLists, self).__init__(seq)
        self.sanity_check()

    @classmethod
    def ensure(cls, seq):
        """ if it's already SentencesAsWordLists, just return it. if not, wrap it (which triggers sanity_check())
        """
        if isinstance(seq, cls):
            return seq
        else:
            return cls(seq)

    def sanity_check(self):
        if self.data:
            if isinstance(self.data[0], basestring) or hasattr(self.data[0], "lower"):
                raise ValueError("should be list-of-lists-of-strings, appears to be list of strings")

    def unwrap(self):
        """ return internal list (useful when we need to pass to something that is over-strict about type-checking)
        """
        try:
            # if self.data is a list of WordList instances, this will work
            return [word_list.unwrap() for word_list in self.data]
        except AttributeError:
            return [word_list for word_list in self.data]

    def __repr__(self):
        return u"SentencesAsWordLists({!r})".format(self.data)


class WordList(UserList):
    """ just a list of strings - with Just Enough sanity checking (yet still permitting duck typing)

        >>> import pytest
        >>> assert WordList(["some", "words"])
        >>> with pytest.raises(ValueError): WordList([["oops", "you", "passed..."], ["a", "sentence", "list"]])
        >>> from presswork.text import clean
        >>> assert WordList([clean.CleanInputString("yee")])
    """

    def __init__(self, seq):
        super(WordList, self).__init__(seq)
        self.sanity_check()

    def sanity_check(self):
        if self.data:
            first_value = self.data[0]
            if (not isinstance(first_value, basestring)) and (not hasattr(first_value, "lower")):
                raise ValueError("should be list of strings")

    def unwrap(self):
        """ return internal list (useful when we need to pass to something that is over-strict about type-checking)
        """
        return self.data
