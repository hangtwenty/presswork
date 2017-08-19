#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" The setup script. Started from excellent boilerplate given by audreyr/cookiecutter-pypackage.
"""
import codecs
import os

from setuptools import setup, find_packages

# setup.py quirk - it's OK to subclass `install` (*IS* actually a class), but must alias to avoid name collision
from setuptools.command.install import install as SetuptoolsInstallCommand

HERE = os.path.abspath(os.path.dirname(__file__))

with codecs.open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

# TODO(hangtwenty) after dust settles from refactor, pip --upgrade some things, re-test, and re-pin
NLTK_VERSION='3.0.2'

_requirements_cli = [
    'Click>=6.0',
]

_requirements_server = [
    'Flask',
    'Flask-WTF',
    'wtforms',
]

# these could all be split up, but really purpose of 'Presswork' is to bring a couple of things together into an
# instant-gratification sandbox. so, a compromise: just make things clear-cut, even though I'm 'bundling' them.
requirements = _requirements_cli + _requirements_server + [
    'funcy==1.4',
    'regex==2015.3.18',  # TODO maybe stop using this dependency and switch to stdlib `re`.

    'nltk==' + NLTK_VERSION,
]

setup_requirements = [
    'pytest-runner',

    # NLTK is required during setup.py if we want to have setup.py download the NLTK corpora.
    'nltk==' + NLTK_VERSION,
]

with codecs.open(os.path.join(HERE, 'requirements_dev.txt'), encoding='utf-8') as f:
    test_requirements = [line.strip() for line in f.read().split('\n')]

_required_nltk_corpora = [
    'punkt',
    'treebank',
]

class InstallWithNLTKCorpora(SetuptoolsInstallCommand):
    """ Extend the behavior of `python setup.py install` to also fetch/install NLTK corpora.

    Where does NLTK data install corpora? NLTK has a few fallback options, so few users need to think about it.
    However if you hit an issue or wish to control it, you can:
        - out-of-box way using NLTK: you can set `NLTK_DATA` environment variable (no code change needed)
        - if you need more info, see official NLTK docs, and/or this thread:
          https://stackoverflow.com/questions/3522372 for more info
    """
    def run(self):
        # setuptools is an oldie goldie. super() is not supported by base class (it's an "old style class")
        SetuptoolsInstallCommand.do_egg_install(self)

        import nltk
        for corpus in _required_nltk_corpora:
            nltk.download(corpus)

setup(
    name='presswork',
    version='0.2.0',
    description="Instant gratification sandbox for text generation using Markov Chains. "
                "A little Flask app (only for local use), and a CLI that supports piping. "
                "Comes with a couple of Markov Chain implementations - pluggable. Have fun!",
    long_description=readme,
    author="Michael Floering",
    author_email='michael.floering@gmail.com',
    url='https://github.com/hangtwenty/presswork',
    packages=find_packages(include=['presswork']),
    entry_points={
        # TODO(hangtwenty) add a CLI that accepts text input on stdin, outputs on stdout (flexible, chainable)
        'console_scripts': [
            'presswork=presswork.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='presswork',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,

    #----------------------------------------------------------------------------------
    # less-common things (not just boilerplate, has to do with this specific project):
    #----------------------------------------------------------------------------------
    cmdclass={
        'install': SetuptoolsInstallCommand,
        'install_with_nltk_corpora': InstallWithNLTKCorpora,
    },
)
