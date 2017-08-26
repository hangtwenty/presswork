import re

from jinja2 import Markup


def newlines_to_br(value):
    """ Converts newlines (and CRs) into HTML: `<br/>`

        >>> newline = chr(10)           # (whitespace is goofy in doctests)
        >>> carriage_return = chr(13)
        >>> str(newlines_to_br(newline))
        '<br/>'
        >>> str(newlines_to_br(carriage_return))
        '<br/>'
        >>> str(newlines_to_br(carriage_return + newline))
        '<br/>'
        >>> str(newlines_to_br("foo" + carriage_return + newline + "bar"))
        'foo<br/>bar'
        >>> str(newlines_to_br(("foo" + newline + "bar" + newline)) * 3)
        'foo<br/>bar<br/>foo<br/>bar<br/>foo<br/>bar<br/>'
    """
    value = re.sub(r'\r\n|\r|\n', '\n', value)  # normalize newlines
    return Markup(value.replace('\n', '<br/>'))


def tabs_to_nbsp(value, tab_size=4):
    """ Converts whitespace tabs to HTML: nonbreaking spaces `&nbsp;`

        >>> tab = chr(9)                # (whitespace is goofy in doctests)
        >>> str(tabs_to_nbsp(tab + 'Indented by 2.', tab_size=2))
        '&nbsp;&nbsp;Indented by 2.'
        >>> str(tabs_to_nbsp(tab + 'Indented by 4.', tab_size=4))
        '&nbsp;&nbsp;&nbsp;&nbsp;Indented by 4.'
    """
    return Markup(value.replace('\t', '&nbsp;' * tab_size))


def multispaces_to_nbsp(value, multiple_size=2):
    """ Converts multiple sequential spaces *two at a time* to HTML: nonbreaking spaces `&nbsp;`

        >>> str(multispaces_to_nbsp('  Indented by 2.', multiple_size=2))
        '&nbsp;&nbsp;Indented by 2.'
        >>> str(multispaces_to_nbsp('    Indented by 4.', multiple_size=4))
        '&nbsp;&nbsp;&nbsp;&nbsp;Indented by 4.'
        >>> str(multispaces_to_nbsp('  Surrounded by 2s.      ', multiple_size=2))
        '&nbsp;&nbsp;Surrounded by 2s.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
        >>> str(multispaces_to_nbsp('    Leftovers not handled    ...     <-- 1 left', multiple_size=4))
        '&nbsp;&nbsp;&nbsp;&nbsp;Leftovers not handled&nbsp;&nbsp;&nbsp;&nbsp;...&nbsp;&nbsp;&nbsp;&nbsp; <-- 1 left'
    """
    return Markup(value.replace(' ' * multiple_size, '&nbsp;' * multiple_size))
