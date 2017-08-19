# -*- coding: utf-8 -*-
""" Download NLTK corpora dependencies
"""
import nltk
import sys

# TODO(hangtwenty) is there a good way to do this as part of setup.py? i.e. try https://stackoverflow.com/questions/26799894/installing-nltk-data-in-setup-py-script
# TODO(hangtwenty) regardless, wire this up to Makefile.
if __name__ == "__main__":
    try:
        download_dir = sys.argv[1]
    except:
        download_dir = None

    nltk.download('punkt', download_dir=download_dir)
    nltk.download('treebank', download_dir=download_dir)
