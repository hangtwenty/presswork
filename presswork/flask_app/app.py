# -*- coding: utf-8 -*-
""" Little Flask app FOR LOCAL USE ONLY, for rapidly playing around with text generation.
"""
import logging
import uuid

from flask import Flask, render_template

# noinspection PyUnresolvedReferences
from flask.ext.wtf import Form
# noinspection PyUnresolvedReferences
from flask.ext.wtf.csrf import CsrfProtect

from wtforms import validators, StringField, IntegerField, SelectField, ValidationError

from presswork import constants
from presswork.sanitize import SanitizedString
from presswork.text import text_makers

from presswork.flask_app import template_filters

app = Flask(__name__)
csrf = CsrfProtect(app=app)
app.config['SECRET_KEY'] = str(uuid.uuid4())

# template filters are a safer way to convert whitespace to HTML, without turning off escaping
app.add_template_filter(template_filters.newlines_to_br, name="newlines_to_br")
app.add_template_filter(template_filters.tabs_to_nbsp, name="tabs_to_nbsp")


logger = logging.getLogger('presswork')

# TODO handle these upgrades/deprecation warnings
# presswork/flask_app/app.py:10: ExtDeprecationWarning: Importing flask.ext.wtf is deprecated, use flask_wtf instead.
#   from flask.ext.wtf import Form
# presswork/flask_app/app.py:12: ExtDeprecationWarning: Importing flask.ext.wtf.csrf is deprecated, use flask_wtf.csrf instead.
#   from flask.ext.wtf.csrf import CsrfProtect
# presswork/flask_app/app.py:21: FlaskWTFDeprecationWarning: "flask_wtf.CsrfProtect" has been renamed to "CSRFProtect" and will be removed in 1.0.
#   csrf = CsrfProtect(app=app)

class MarkovChainTextMakerForm(Form):
    text = StringField(
        'Input text',
        validators=[
            validators.InputRequired(),
            validators.Length(max=1000000) # XXX: this limit was picked arbitrarily, not by observation nor testing
        ]
    )

    state_size = IntegerField(
        "N-gram size AKA state size AKA window size (increase for more 'rigid' modeling of input text)",
        validators=[validators.NumberRange(min=1, max=6)],
        default=constants.DEFAULT_NGRAM_SIZE, )

    count_of_sentences_to_make = IntegerField(
        "Number of sentences to generate", [validators.NumberRange(min=1, max=3000)], default=50, )

    # TODO(hangtwenty) joiners flexibility - do it in text.text_makers (see dev_memos/Composer) then expose here

    # XXX really this should be a SelectField but WTForms was being the pain and I want to handle other things first.
    # (while I like the micro-ness of Flask for purposes this, forms are often a pain...)
    strategy = StringField(
            "Strategy (leave this as default, usually) (choices: {})".format(", ".join(text_makers.CLASS_NICKNAMES)),
            validators=[validators.InputRequired(),validators.Length(max=20),],
            default=text_makers.DefaultTextMaker.NICKNAME)

    # TODO(hangtwenty) test_app should have a test of this - input 'bogus' and get validationerror on page
    def validate_strategy(form, field):
        strategy = field.data.lower()
        if strategy not in text_makers.CLASS_NICKNAMES:
            raise ValidationError('strategy must be one of: {}'.format(strategy))


@app.route("/", methods=['GET', 'POST', ])
def markov():
    form = MarkovChainTextMakerForm()

    if form.validate_on_submit():
        logger.info(u'[flask] received valid form submission')

        state_size = form.state_size.data
        input_text = SanitizedString(form.text.data)
        strategy = SanitizedString(form.strategy.data)
        count_of_sentences_to_make = form.count_of_sentences_to_make.data

        # keep last submission in the text fields (supports 'accumulating' workflow)
        # (you'd  think there'd be a cleaner way - I recall trying the WTForms way and it not working for me)
        for field_name in ('text', 'state_size', 'count_of_sentences_to_make', 'strategy'):
            field = getattr(form, field_name)
            if field.data:
                field.default = field.data

        logger.info(u'[flask] notable form parameters: state_size={}, count_of_sentences_to_make={} '
                    u'(input text shown at DEBUG level)'.format(state_size, count_of_sentences_to_make))

        text_maker = text_makers.create_text_maker(
                input_text,
                class_or_nickname=strategy,
                state_size=state_size,)
        # TODO, text_made is just lists still, not joined, so I'm joining here...
        # TODO instead of joining here, should be using common utils, from text.text_makers (see dev_memos/Composer)
        # TODO allllllllllsooooooooo have to actually do the <br/> etc in the template, or it gets escaped
        #       and honestly even though this isn't a serious app, I am so allergic to turning autoescape off :sweat_smile:
        # probably this is what I need, https://gist.github.com/cemk/1324543
        text_body = text_makers.rejoin(text_maker.make_sentences(count=count_of_sentences_to_make))
        text_title = text_makers.rejoin(text_maker.make_sentences(count=1))

        return render_template(
            'index.html', form=form, text_made=text_body, text_made_title=text_title)

    return render_template('index.html', form=form)


if __name__ == "__main__":
    import sys

    from presswork.log import setup_logging
    setup_logging()

    try:
        port = sys.argv[1]
    except IndexError:
        port = 5000

    app.run('0.0.0.0', port=port)
