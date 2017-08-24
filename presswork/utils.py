import collections


def iter_flatten(lst):
    """ flatten nested lists (but do not descend into strings)

    >>> list(iter_flatten([['a', 'sentence', '~=', 'a', 'sequence', 'of', 'words.'], [u'another', u'sentence']]))
    ['a', 'sentence', '~=', 'a', 'sequence', 'of', 'words.', u'another', u'sentence']
    >>> list(iter_flatten([[[[[[[[[[[[[[[[[[[[[[[[[[['very nested']]]]]]]]]]]]]]]]]]]]]]], 'foo'], 'bar'], 'baz']]))
    ['very nested', 'foo', 'bar', 'baz']
    >>> import pytest
    >>> with pytest.raises(ValueError): list(iter_flatten("can't just pass string"))
    """
    if isinstance(lst, basestring):
        raise ValueError("meant to handle lists of (lists of (lists of...)) strings. rejecting to avoid confusion")

    for element in lst:
        if isinstance(element, collections.Iterable) and not isinstance(element, basestring):
            for sub in iter_flatten(element):
                yield sub
        else:
            yield element