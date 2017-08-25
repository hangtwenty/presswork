# -*- coding: utf-8 -*-
""" Little Flask app FOR LOCAL USE ONLY, for rapidly playing around with text generation.
"""
import logging
import uuid

from flask import Flask, render_template

from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect

from wtforms import validators, StringField, IntegerField, ValidationError

from presswork import constants
from presswork.sanitize import SanitizedString
from presswork.text import grammar
from presswork.text import text_makers

from presswork.flask_app import template_filters

app = Flask(__name__)
csrf = CSRFProtect(app=app)
app.config['SECRET_KEY'] = str(uuid.uuid4())

# template filters are a safer way to convert whitespace to HTML, without turning off escaping
app.add_template_filter(template_filters.newlines_to_br, name="newlines_to_br")
app.add_template_filter(template_filters.tabs_to_nbsp, name="tabs_to_nbsp")

logger = logging.getLogger('presswork')


class MarkovChainTextMakerForm(FlaskForm):
    input_text = StringField(
            'Input text',
            validators=[
                validators.InputRequired(),
                validators.Length(max=1000000)  # XXX: this limit was picked arbitrarily, not by observation nor testing
            ]
    )

    ngram_size = IntegerField(
            "N-gram size AKA state size AKA window size (increase for more 'rigid' modeling of input text)",
            validators=[validators.NumberRange(min=1, max=6)],
            default=constants.DEFAULT_NGRAM_SIZE, )

    count_of_sentences_to_make = IntegerField(
            "Number of sentences to generate", [validators.NumberRange(min=1, max=3000)], default=50, )

    # XXX really this should be a SelectField but WTForms was being the pain and I want to handle other things first.
    # (while I like the micro-ness of Flask for purposes this, forms are often a pain...)
    text_maker_strategy = StringField(
            "Markov Chain Strategy | choices: {} | Usually leave this as default. "
            "If markovify gives you issues with Unicode try pymc. ".format(
                    ", ".join(text_makers.TEXT_MAKER_NICKNAMES)),
            validators=[validators.InputRequired(), validators.Length(max=20), ],
            default=text_makers.DEFAULT_TEXT_MAKER_NICKNAME)

    tokenizer_strategy = StringField(
            "Tokenizer Strategy | choices: {} | NLTK is most versatile but slower. Markovify tokenizer "
            "is fast but narrow. (Only use 'whitespace' tokenizer when your input is 1 sentence per line.)".format(
                    ", ".join(grammar.TOKENIZER_NICKNAMES)),
            validators=[validators.InputRequired(), validators.Length(max=20), ],
            default='nltk')

    def validate_text_maker_strategy(form, field):
        text_maker_strategy = field.data.lower()
        if text_maker_strategy not in text_makers.TEXT_MAKER_NICKNAMES:
            raise ValidationError(
                    'text_maker_strategy must be one of: {}'.format(", ".join(text_makers.TEXT_MAKER_NICKNAMES)))

    def validate_tokenizer_strategy(form, field):
        tokenizer_strategy = field.data.lower()
        if tokenizer_strategy not in grammar.TOKENIZER_NICKNAMES:
            raise ValidationError(
                    'tokenizer_strategy must be one of: {}'.format(", ".join(grammar.TOKENIZER_NICKNAMES)))


@app.route("/", methods=['GET', 'POST', ])
def markov():
    form = MarkovChainTextMakerForm()

    if form.validate_on_submit():
        logger.info(u'[flask] received valid form submission')

        # (Flask doesn't do forms, so you use WTForms. WTForms is great in some ways, but definitely verbose.)
        ngram_size = form.ngram_size.data
        input_text = SanitizedString(form.input_text.data)
        text_maker_strategy = SanitizedString(form.text_maker_strategy.data)
        tokenizer_strategy = SanitizedString(form.tokenizer_strategy.data)
        count_of_sentences_to_make = form.count_of_sentences_to_make.data

        # keep last submission in the text fields (supports 'accumulating' workflow)
        for field_name in (
                'input_text', 'ngram_size', 'count_of_sentences_to_make', 'text_maker_strategy', 'tokenizer_strategy'):
            field = getattr(form, field_name)
            if field.data:
                field.default = field.data

        logger.info(u'[flask] notable form parameters: ngram_size={}, count_of_sentences_to_make={} '
                    u'(input text shown at DEBUG level)'.format(ngram_size, count_of_sentences_to_make))

        text_maker = text_makers.create_text_maker(
                input_text=input_text,
                strategy=text_maker_strategy,
                sentence_tokenizer=tokenizer_strategy,
                ngram_size=ngram_size, )

        generated_text_body = grammar.rejoin(text_maker.make_sentences(count=count_of_sentences_to_make))
        generated_text_title = grammar.rejoin(text_maker.make_sentences(count=1))

        return render_template(
                'index.html', form=form, generated_text=generated_text_body, generated_text_title=generated_text_title)

    return render_template('index.html', form=form)


if __name__ == "__main__":  # pragma: no cover
    """ development-only server. will run in Flask's wonderful, wonderful debug mode if you give it "--debug"
    """
    import os
    import sys

    from presswork.log import setup_logging

    setup_logging()

    try:
        port = sys.argv[1]
    except IndexError:
        port = 5000

    app.run('127.0.0.1', port=port, debug=(os.environ.get("DEBUG", None) is not None))
