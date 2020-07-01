import logging.config
import os

import coloredlogs


def add_logger():
    def wrapper(cls):

        cls._logger = logging.getLogger(cls.__name__)

        return cls
    return wrapper


class SMRFLogger():
    """Setup the root logger for SMRF

    Raises:
        ValueError: [description]
    """

    FMT = '%(levelname)s:%(name)s:%(message)s'

    def __init__(self, config):

        self.log_level = config.get('log_level', 'info').upper()

        numeric_level = getattr(logging, self.log_level, None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: {}'.format(self.log_level))

        # setup the logging
        self.log_file = config.get('log_file', None)
        if self.log_file is not None:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            # From the python3 docs on basicConfig
            # "This function does nothing if the root logger already has
            # handlers configured"
            # for handler in logging.root.handlers[:]:
            #     logging.root.removeHandler(handler)

            # logging.basicConfig(filename=self.log_file,
            #                     level=numeric_level,
            #                     filemode='a',
            #                     format=self.FMT)
        # else:
            # logging.basicConfig(level=numeric_level)
            # coloredlogs.install(level=numeric_level, fmt=self.FMT)

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
                },
            },
            'loggers': {
                '': {  # root logger
                    'handlers': ['default'],
                    'level': self.log_level,
                    'propagate': False
                }
            }
        }

        logging.config.dictConfig(log_config)
