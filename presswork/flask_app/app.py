# -*- coding: utf-8 -*-
""" Little Flask app FOR LOCAL USE ONLY, for rapidly playing around with text generation.
"""
import logging
import uuid

from flask import Flask, render_template
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import validators, StringField, IntegerField, ValidationError, TextAreaField

from presswork import constants
from presswork.text import clean
from presswork.text import text_makers
from presswork.text.grammar import joiners
from presswork.text.grammar import tokenizers

app = Flask(__name__)
csrf = CSRFProtect(app=app)
app.config['SECRET_KEY'] = str(uuid.uuid4())

logger = logging.getLogger('presswork')


def lower_or_empty(s):
    return (s or u"").lower()


class MarkovChainTextMakerForm(FlaskForm):
    """ a form for the parameters to `text_makers.create_text_maker` (or most of them)
    """
    input_text = TextAreaField('Input text', validators=[validators.InputRequired()])

    ngram_size = IntegerField(
            "N-gram size AKA state size AKA window size (increase for more 'rigid' modeling of input text)",
            validators=[validators.NumberRange(min=1, max=6)],
            default=constants.DEFAULT_NGRAM_SIZE, )

    count_of_sentences_to_make = IntegerField(
            "Number of sentences to generate", [validators.NumberRange(min=1, max=3000)], default=50, )

    # NOTE: really this should be a SelectField but WTForms was being difficult and I want to handle other things first.
    text_maker_strategy = StringField(
            "Markov Chain Strategy | choices: {} | markovify is first preference, pymc second. ".format(
                    ", ".join(text_makers.TEXT_MAKER_NICKNAMES)),
            validators=[validators.InputRequired(), validators.Length(max=20), ],
            filters=[lower_or_empty],
            default=text_makers.DEFAULT_TEXT_MAKER_NICKNAME)

    tokenizer_strategy = StringField(
            "Tokenizer Strategy | choices: {} | NLTK is most versatile but slower. Markovify tokenizer "
            "is fast but narrow. 'just_whitespace' is simplest but requires line-separated input.".format(
                    ", ".join(tokenizers.TOKENIZER_NICKNAMES)),
            validators=[validators.InputRequired(), validators.Length(max=20), ],
            filters=[lower_or_empty],
            default='nltk')

    joiner_strategy = StringField(
            "Joiner Strategy | choices: {}".format(", ".join(joiners.JOINER_NICKNAMES)),
            validators=[validators.InputRequired(), validators.Length(max=20), ],
            filters=[lower_or_empty],
            default='nltk')

    def validate_text_maker_strategy(form, field):
        if field.data not in text_makers.TEXT_MAKER_NICKNAMES:
            raise ValidationError(
                    'text_maker_strategy must be one of: {}'.format(", ".join(text_makers.TEXT_MAKER_NICKNAMES)))

    def validate_tokenizer_strategy(form, field):
        if field.data not in tokenizers.TOKENIZER_NICKNAMES:
            raise ValidationError(
                    'tokenizer_strategy must be one of: {}'.format(", ".join(tokenizers.TOKENIZER_NICKNAMES)))

    def validate_joiner_strategy(form, field):
        if field.data not in joiners.JOINER_NICKNAMES:
            raise ValidationError(
                    'joiner_strategy must be one of: {}'.format(", ".join(
                            joiners.JOINER_NICKNAMES)))

    def debug_log(self):
        if logger.isEnabledFor(logging.DEBUG):
            for field in self:
                logger.debug(u'[flask] form.{} :\n{}\n'.format(field.name, field.data))


@app.route("/", methods=['GET', 'POST', ])
def markov():
    form = MarkovChainTextMakerForm()
    form.debug_log()

    if form.validate_on_submit():
        logger.info(u'[flask] received valid form submission')

        data = {
            field.name: (clean.CleanInputString(field.data) if isinstance(field.data, basestring) else field.data)
            for field in iter(form)
            }

        text_maker = text_makers.create_text_maker(
                input_text=data['input_text'],
                strategy=data['text_maker_strategy'],
                sentence_tokenizer=data['tokenizer_strategy'],
                joiner=data['joiner_strategy'],
                ngram_size=data['ngram_size'],
        )

        generated_text_title = text_maker.join(text_maker.make_sentences(count=1))
        generated_text_body = text_maker.join(text_maker.make_sentences(count=data['count_of_sentences_to_make']))

        generated_text_body = text_maker.proofread(generated_text_body)
        generated_text_title = text_maker.proofread(generated_text_title)

        for field in iter(form):
            # make the fields 'sticky' by keeping values from last submission
            if not field.name.lower().startswith('csrf'):
                field.default = field.data

        return render_template(
                'index.html', form=form, generated_text=generated_text_body, generated_text_title=generated_text_title)

    return render_template('index.html', form=form)


if __name__ == "__main__":  # pragma: no cover
    """ development-only server. will run in Flask's wonderful, wonderful debug mode if you set "DEBUG" var beforehand

    $ DEBUG=1 python presswork/flask_app/app.py 5000
    """
    import datetime
    import os
    import sys

    from presswork.log import setup_logging

    debug_mode = os.environ.get("DEBUG", None) is not None

    setup_logging()
    if debug_mode:
        logger.setLevel(logging.DEBUG)

    try:
        port = int(sys.argv[1])
    except IndexError:
        port = 5000

    msg = u'[flask] started on {} at {}'.format(port, datetime.datetime.now())
    logger.info(msg)
    print msg

    app.run('127.0.0.1', port=port, debug=debug_mode)
