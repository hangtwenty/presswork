import pytest

from presswork.text import text_makers


@pytest.fixture(params=text_makers.TEXT_MAKER_NICKNAMES)
def each_text_maker(request):
    """ get 1 text maker instance (doesn't load input_text; so, test cases control input_text, ngram_size)

    the fixture is parametrized so that test cases will get 'each' text_maker, 1 per test case

    this fixture should be used in tests where the criteria isn't specific to the text maker implementation,
    such as these essentials/parity texts.
    """
    name = request.param
    text_maker = text_makers.create_text_maker(strategy=name)
    return text_maker


@pytest.fixture()
def all_text_makers(request):
    """ get instances of ALL text maker variants (doesn't load input_text; test cases control input_text, ngram_size)

    this fixture should be used when we want multiple text maker varieties in one test, such as to confirm that
    under valid circumstances they behave similar (or same) for similar inputs
    """
    all_text_makers = []
    for name in text_makers.TEXT_MAKER_NICKNAMES:
        text_maker = text_makers.create_text_maker(strategy=name)
        all_text_makers.append(text_maker)

    return all_text_makers
