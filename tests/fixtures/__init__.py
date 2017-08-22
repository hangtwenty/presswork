# -*- coding: utf-8 -*-
""" expose the plaintext files here. keep it simple/dumb here, just making this folder 'take care of itself'

don't put pytest fixtures here, instead see `tests/conftest.py` where that will be wired up.
"""
import os
import os.path

HERE = os.path.abspath(os.path.dirname(__file__))


def get_abs_path_to_files_in_subfolder(subfolder, parent_folder=os.path.join(HERE, 'plaintext')):
    basenames = os.listdir(os.path.join(parent_folder, subfolder))
    if not basenames:
        raise IOError("expected 1+ plaintext files in {}/{}".format(parent_folder, subfolder))
    return [os.path.join(parent_folder, subfolder, basename) for basename in basenames]


FILENAMES_NEWLINES = get_abs_path_to_files_in_subfolder('newlines')
FILENAMES_PROSE = get_abs_path_to_files_in_subfolder('prose')
FILENAMES_MIXED = get_abs_path_to_files_in_subfolder('mixed')

if __name__ == "__main__":
    # need to troubleshoot? just run like `python tests/fixtures` and get some info.
    import pprint

    pprint.pprint(locals())
