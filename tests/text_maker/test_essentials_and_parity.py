import pytest


from presswork.text import text_makers


@pytest.fixture(params=text_makers.CLASS_NICKNAMES)
def each_text_maker(request):
    """ get 1 text maker instance (doesn't load input_text, so that test cases control state_size, input_text)

    the fixture is parametrized so that test cases will get 'each' text_maker, 1 per test case

    this fixture should be used in tests where the criteria isn't specific to the text maker implementation,
    such as these essentials/parity texts.
    """
    name = request.param
    text_maker = text_makers.create_text_maker(
        class_or_nickname=name,
    )
    return text_maker

def test_locked_after_input_text(each_text_maker):
    text_maker = each_text_maker
    text_maker.input_text("Foo bar baz. Foo bar quux.")

    with pytest.raises(text_makers.TextMakerIsLockedException):
        text_maker.input_text("This should not be loaded")

    output = text_maker.make_sentences(50)

    # TODO in TextMaker before returning from underlying ting, should be converting (just wrapping?)
    #  SentencesOfWords and that should have __str__ that calls rejoiner,
    # i mean it's OK to abuse the stringification here for a little ,but htis is a good case for cleaning that up
    # and i think the implementation will look nice

    assert "This" not in output
    assert "loaded" not in output

def test_cannot_change_state_size_after_inputting_text(each_text_maker):
    text_maker = each_text_maker
    text_maker.state_size = 4 # this is allowed, it is not locked yet...

    text_maker.input_text("Foo bar blah baz. Foo bar blah quux.")
    with pytest.raises(text_makers.TextMakerIsLockedException):
        text_maker.state_size = 3


def test_avoid_pollution_between_instances(each_text_maker):
    """ helps to confirm a design goal - of the instances being isolated, despite issues with underlying strategies

    two ways pollution between the instances could happen (both observed with PyMarkovChain for example):
        a) both sharing same disk persistence for the model, too automatically (now disabled)
        b) if not careful about how 2+ are set up/copied, ".strategy" could be pointer to same instance of underlying
        strategy - TextMaker.copy() added to help avoid this

    so this test case avoids regressions in (a) mainly. point (b) is helpful to this test case and normal usage,
    so might as well exercise it here
    """
    text_maker_1 = each_text_maker
    text_maker_2 = text_maker_1.clone()

    text_maker_1.input_text("Foo bar baz. Foo bar quux.")
    text_maker_2.input_text("Input text for 2 / Input text does not go to 1 / class does not share from 1")

    assert 'Foo' in str(text_maker_1.make_sentences(10))
    assert 'Foo' not in str(text_maker_2.make_sentences(10))

    assert 'Input' in str(text_maker_2.make_sentences(10))
    assert 'Input' not in str(text_maker_1.make_sentences(10))





