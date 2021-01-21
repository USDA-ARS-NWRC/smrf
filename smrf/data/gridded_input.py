import logging


class GriddedInput:
    TYPE = 'gridded'

    def __init__(self,
                 start_date, end_date,
                 bbox=None, topo=None, config=None):

        self.start_date = start_date
        self.end_date = end_date
        self.time_zone = start_date.tzinfo

        self.__set_attribute('topo', topo)
        self.__set_attribute('bbox', bbox)
        self.__set_attribute('config', config)

        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def bbox(self):
        return self._bbox

    @property
    def config(self):
        return self._config

    @property
    def topo(self):
        return self._topo

    def __set_attribute(self, attribute, argument):
        if argument is None:
            raise TypeError('Missing argument: %s' % attribute)
        else:
            setattr(self, '_%s' % attribute, argument)
