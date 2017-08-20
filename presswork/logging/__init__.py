import logging
import logging.config
import os

import yaml

HERE = os.path.abspath(os.path.dirname(__file__))

_PRESSWORK_LOGGING_HAS_BEEN_SET_UP = False

def setup_logging(path_to_logging_yaml=os.path.join(HERE, "logging.yaml")):
    """Setup logging configuration
    """
    global _PRESSWORK_LOGGING_HAS_BEEN_SET_UP
    if _PRESSWORK_LOGGING_HAS_BEEN_SET_UP:
        logger = logging.getLogger('presswork')
        logger.warning('setup_logging() has already been called! short-circuiting and returning with no changes.')
        return

    if path_to_logging_yaml:
        with open(path_to_logging_yaml, 'r') as f:
            config = yaml.load(f)
    else:
        raise ValueError("config_path needs to be a path to a YAML logging config. "
                         "see logging.yaml in this directory for a starter")

    logging.config.dictConfig(config)

    _PRESSWORK_LOGGING_HAS_BEEN_SET_UP = True

    return logging.getLogger('presswork')
