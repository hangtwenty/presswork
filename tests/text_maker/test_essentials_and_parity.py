# -*- coding: utf-8 -*-
import pytest


from presswork.text import text_makers


@pytest.fixture(params=text_makers.CLASS_NICKNAMES)
def each_text_maker(request):
    """ get 1 text maker instance (doesn't load input_text; so, test cases control input_text, state_size)

    the fixture is parametrized so that test cases will get 'each' text_maker, 1 per test case

    this fixture should be used in tests where the criteria isn't specific to the text maker implementation,
    such as these essentials/parity texts.
    """
    name = request.param
    text_maker = text_makers.create_text_maker(class_or_nickname=name)
    return text_maker

@pytest.fixture()
def all_text_makers(request):
    """ get instances of ALL text maker variants (doesn't load input_text; test cases control input_text, state_size)

    this fixture should be used when we want multiple text maker varieties in one test, such as to confirm that
    under valid circumstances they behave similar (or same) for similar inputs
    """
    all_text_makers = []
    for name in text_makers.CLASS_NICKNAMES:
        text_maker = text_makers.create_text_maker(class_or_nickname=name)
        all_text_makers.append(text_maker)

    return all_text_makers


@pytest.mark.parametrize('state_size', [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
def test_easy_deterministic_case_are_same_for_all_text_makers(all_text_makers, text_easy_deterministic, state_size):
    """ Any TextMaker will return deterministic results from seq of words w/ no duplicates; all strategies should match

    (very high state_sizes aren't very useful, but just checking that sparks don't fly for no good reason)
    """

    # let's throw unicode on end of each just to cover unicode too (pytest.fixture(params=...) only accepts ASCII)
    input_text = text_easy_deterministic + u" plus_ünicôde"

    outputs = {}
    for text_maker in all_text_makers:
        text_maker.state_size = state_size
        text_maker.input_text(text_easy_deterministic)

        outputs[text_maker.NICKNAME] = text_maker.make_sentences(1)

    # expected is that all text makers output same deterministic sentence for these inputs.
    # we can check that pretty elegantly by stringifying, calling set, and making sure their is only 1 unique output
    outputs_rejoined = {name: text_makers.rejoin(output).strip() for name, output in outputs.items()}
    assert len(set(outputs_rejoined.values())) == 1



def test_locked_after_input_text(each_text_maker):
    text_maker = each_text_maker
    text_maker.input_text("Foo bar baz. Foo bar quux.")

    with pytest.raises(text_makers.TextMakerIsLockedException):
        text_maker.input_text("This should not be loaded")

    output = text_maker.make_sentences(50)

    assert "This" not in text_makers.rejoin(output)
    assert "loaded" not in text_makers.rejoin(output)

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





