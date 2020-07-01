import logging.config
import os

import coloredlogs


class SMRFLogger():
    """Setup the root logger for SMRF to either the console or
    to a file
    """

    FMT = '%(levelname)s:%(name)s:%(message)s'

    def __init__(self, config):

        self.log_level = config.get('log_level', 'info').upper()
        self.log_file = config.get('log_file', None)

        # https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema
        log_config = {
            'version': 1,
            'formatters': {
                'standard': {
                    'format': self.FMT
                }
            },
            'handlers': {
                'default': {
                    'level': self.log_level,
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout',  # Default is stderr
                }
            },
            'loggers': {
                '': {  # root logger
                    'handlers': ['default'],
                    'level': self.log_level,
                    'propagate': False
                }
            }
        }

        if self.log_file is not None:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            log_config['handlers']['log_file'] = {
                'level': self.log_level,
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': self.log_file,
                'mode': 'a'
            }

            log_config['loggers']['']['handlers'] = ['log_file']

        logging.config.dictConfig(log_config)

        if self.log_file is None:
            coloredlogs.install(level=self.log_level, fmt=self.FMT)
