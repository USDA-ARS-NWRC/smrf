from copy import deepcopy
import unittest
import pandas as pd
import numpy as np

from smrf.envphys import radiation
from tests.test_configurations import SMRFTestCase

from pysolar.solar import get_altitude, get_azimuth


class TestRadiation(SMRFTestCase):

    def test_sunang(self):
        """ Sunang calculation """

        # replicate the sun angle calculation from the sunang man page
        # for Santa Barbara on Feb 15, 1990 at 20:30 UTC
        # The difference between IPW sunang and Pysolar for the following
        # example are:
        #           | IPW       | PySolar
        # zenith    | 47.122    | 47.107
        # cosz      | 0.680436  | 0.680631
        # azimuth   | -5.413    | -5.416
        #
        # The differences for this one instance is hundredths of degrees
        # in zenith and thousandths in azimuth

        date_time = pd.to_datetime('2/15/1990 20:30')
        date_time = date_time.tz_localize('UTC')
        lat = 34.416667
        lon = -119.9
        cosz = 0.680436
        zenith = 47.122
        az = -5.413
        result = radiation.sunang(date_time, lat, lon)

        self.assertTrue(result[0] == cosz)
        self.assertTrue(result[1] == az)

        result = radiation.pysolar_sunang(date_time, lat, lon)

        self.assertTrue(result[0] == cosz)
        self.assertTrue(result[1] == az)
