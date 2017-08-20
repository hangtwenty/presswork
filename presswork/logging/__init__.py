import logging
import logging.config
import os

import yaml

HERE = os.path.abspath(os.path.dirname(__file__))

def setup_logging(config_path=os.path.join(HERE, "logging.yaml"), config=None):
    """Setup logging configuration
    """
    logging.basicConfig()

    error_message = "please supply (only) one of: config (dict), config_path (path to YAML)"
    if config and config_path:
        raise ValueError(error_message)

    if config:
        pass
    elif config_path:
        with open(config_path, 'r') as f:
            config = yaml.load(f)
    else:
        raise ValueError(error_message)

    logging.config.dictConfig(config)
