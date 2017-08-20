# -*- coding: utf-8 -*-
""" Little Flask app FOR LOCAL USE ONLY, for rapidly playing around with text generation.
"""
import logging
import uuid

from flask import Flask, render_template
from flask.ext.wtf import Form
from flask.ext.wtf.csrf import CsrfProtect
from wtforms import validators, StringField, \
    IntegerField

# TODO(hangtwenty) swap this out for general TextMaker/subclasses, and in the form allow changing which one is used
from presswork.text_maker._pymarkovchain_fork import PyMarkovChainWithNLTK

app = Flask(__name__)
csrf = CsrfProtect(app=app)
app.config['SECRET_KEY'] = str(uuid.uuid4())

logger = logging.getLogger('presswork')

class MarkovChainTextMakerForm(Form):
    text = StringField(
        'Input text',
        [
            validators.InputRequired(),
            validators.Length(max=1000000) # XXX: this limit was picked arbitrarily, not by observation nor testing
        ]
    )

    state_size = IntegerField(
        "Window size AKA state size AKA N-Gram Size (increase for more 'rigid' modeling of input text)",
        [validators.NumberRange(min=1, max=9)],
        default=2, )

    count_of_sentences_to_make = IntegerField(
        "Number of sentences to generate", [validators.NumberRange(min=1, max=3000)], default=25, )

    # TODO(hangtwenty) instead of always just join_with=<space>, should give option to specify join characters,
    # max length 100 ... " " is valid ... "\n" gets replaced by newline... unicode gets rejected


@app.route("/", methods=['GET', 'POST', ])
def markov():
    form = MarkovChainTextMakerForm()
    if form.validate_on_submit():
        logger.info('received valid form submission')

        state_size = form.state_size.data
        input_text = form.text.data
        count_of_sentences_to_make = form.count_of_sentences_to_make.data

        # keep last submission in the text fields (supports 'accumulating' workflow)
        # (there is probably a cleaner way to do this with WTForms)
        for field_name in ('text', 'state_size', 'count_of_sentences_to_make'):
            field = getattr(form, field_name)
            if field.data:
                field.default = field.data

        logger.info('notable form parameters: state_size={}, count_of_sentences_to_make={} '
                    '(input text shown at DEBUG level)'.format(state_size, count_of_sentences_to_make))
        logger.debug('input_text=\n{}'.format(input_text))

        text_maker = PyMarkovChainWithNLTK(db_file_path=None, window=state_size)
        text_maker.database_init(input_text)
        text_made = text_maker.make_sentences(count_of_sentences_to_make)
        text_made_title = text_maker.make_sentence().strip('.')

        return render_template(
            'index.html', form=form, text_made=text_made, text_made_title=text_made_title)

    return render_template('index.html', form=form)


if __name__ == "__main__":
    import sys
    try:
        port = sys.argv[1]
    except IndexError:
        port = 5000

    app.run('0.0.0.0', port=port)
