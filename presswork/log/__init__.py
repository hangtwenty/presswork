# -*- coding: utf-8 -*-
""" boilerplate to set up logging cleanly and avoid redundant setup (which can have unintended side-effects)

note, this module is intentionally not called `logging`, as that can mask stdlib `logging` - at least when
certain dynamic importers run like PyCharm's test runner. leave it as `log` ;-)
"""
import logging
import logging.config
import os

import yaml

HERE = os.path.abspath(os.path.dirname(__file__))

PRESSWORK_LOGGING_HAS_BEEN_SET_UP = False

def setup_logging(path_to_logging_yaml=os.path.join(HERE, "logging.yaml")):
    """Setup logging configuration
    """
    global PRESSWORK_LOGGING_HAS_BEEN_SET_UP
    if PRESSWORK_LOGGING_HAS_BEEN_SET_UP:
        logger = logging.getLogger('presswork')
        logger.warning('setup_logging() has already been called! short-circuiting and returning with no changes.')
        return logger

    if path_to_logging_yaml:
        with open(path_to_logging_yaml, 'r') as f:
            config = yaml.load(f)
    else:
        raise ValueError("config_path needs to be a path to a YAML logging config. "
                         "see logging.yaml in this directory for a starter")

    logging.config.dictConfig(config)

    PRESSWORK_LOGGING_HAS_BEEN_SET_UP = True

    return logging.getLogger('presswork')
