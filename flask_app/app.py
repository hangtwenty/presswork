# -*- coding: utf-8 -*-
""" Little Flask server to expose the MarkovChainTextMaker

"""
import uuid

from flask import Flask, render_template
from flask.ext.wtf import Form
from flask.ext.wtf.csrf import CsrfProtect
from wtforms import validators, StringField, \
    IntegerField

from presswork.presswork import MarkovChainTextMaker

app = Flask(__name__)
csrf = CsrfProtect(app=app)
app.config['SECRET_KEY'] = str(uuid.uuid4())


class MarkovChainTextMakerForm(Form):
    text = StringField(
        'Source text',
        [validators.InputRequired(), validators.Length(max=1000000)])

    window = IntegerField(
        "Window size (informally, 'strictness')",
        [validators.NumberRange(min=1, max=9)],
        default=2, )

    count_of_sentences_to_make = IntegerField(
        "Number of sentences to generate", [validators.NumberRange(min=1, max=3000)], default=25, )


@app.route("/", methods=['GET', 'POST', ])
def markov():
    form = MarkovChainTextMakerForm()
    if form.validate_on_submit():
        text_maker = MarkovChainTextMaker(db_file_path=None, window=form.window.data)
        text_maker.database_init(form.text.data)
        text_made = text_maker.make_sentences(form.count_of_sentences_to_make.data)
        text_made_title = text_maker.make_sentence().strip('.')

        for field_name in ('text', 'window', 'count_of_sentences_to_make'):
            field = getattr(form, field_name)
            field.default = field.data

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
