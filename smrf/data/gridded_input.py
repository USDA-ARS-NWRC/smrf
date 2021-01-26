import logging
from datetime import datetime

from smrf.data.load_topo import Topo


class GriddedInput:
    TYPE = 'gridded'

    def __init__(self, start_date, end_date, bbox, topo, config):

        self.start_date = start_date
        self.end_date = end_date

        self.topo = topo
        self.bbox = bbox

        self.config = config

        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, value):
        if not isinstance(value, datetime):
            raise TypeError('Argument start_date is not an instance of %s',
                            datetime.__name__)
        else:
            self._start_date = value

    @property
    def time_zone(self):
        return self.start_date.tzinfo

    @property
    def bbox(self):
        return self._bbox

    @bbox.setter
    def bbox(self, value):
        if len(value) != 4:
            raise TypeError('Argument bbox is not in form of '
                            '[lonmin, latmin, lonmax, latmax]')
        else:
            self._bbox = value

    @property
    def topo(self):
        return self._topo

    @topo.setter
    def topo(self, value):
        if not isinstance(value, Topo):
            raise TypeError('Argument topo is not an instance of %s',
                            Topo.__name__)
        else:
            self._topo = value
