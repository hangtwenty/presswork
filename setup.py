#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: make this work.

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='presswork',
    version='0.1.0',
    description="Presswork is a Markov Chain text generator for impersonating prose and journalistic writing",
    long_description=readme,
    author="hangtwenty",
    url='https://github.com/hangtwenty/presswork',
    packages=[
        'presswork',
    ],
    package_dir={'presswork': 'presswork'},
    include_package_data=True,
    install_requires=requirements,
    license="WTFPL",
    zip_safe=False,
    keywords='presswork',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
