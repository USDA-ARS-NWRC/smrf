from copy import deepcopy
from inicheck.tools import cast_all_variables
from inicheck.utilities import pcfg
import unittest
import pandas as pd

from smrf.envphys import radiation
from tests.test_configurations import SMRFTestCase


class TestRadiation(SMRFTestCase):

    def test_sunang(self):
        """ Sunang calculation """

        # replicate the sun angle calculation from the sunang man page
        # for Santa Barbara on Feb 15, 1990 at 20:30 UTC

        date_time = pd.to_datetime('2/15/1990 20:30')
        result = radiation.sunang(date_time, 34.416667, -119.9)       

        self.assertTrue(result[0] == 0.680436)
        self.assertTrue(result[1] == -5.413)
