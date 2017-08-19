#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script. Started from excellent boilerplate given by audreyr/cookiecutter-pypackage."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    'Click>=6.0',
]

setup_requirements = [
    'pytest-runner',
]

test_requirements = [
    'pytest',
]

setup(
    name='presswork',
    version='0.2.0',
    description="Little interactive tool(s) for text generation using Markov chains. A little Flask app (only for local use), and a CLI. Markov implementations are separate and pluggable. Have fun!",
    long_description=readme,
    author="Michael Floering",
    author_email='michael.floering@gmail.com',
    url='https://github.com/hangtwenty/presswork',
    packages=find_packages(include=['presswork']),
    entry_points={
        # # TODO(hangtwenty) add a CLI that accepts text input on stdin, outputs on stdout (flexible, chainable)
        # 'console_scripts': [
        #     'presswork=presswork.cli:main'
        # ]
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
)
