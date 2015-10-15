# -*- coding: utf-8 -*-
""" Download corpora dependencies
"""
import nltk
import sys

if __name__ == "__main__":
    try:
        download_dir = sys.argv[1]
    except:
        download_dir = None

    nltk.download('punkt', download_dir=download_dir)
    nltk.download('treebank', download_dir=download_dir)
