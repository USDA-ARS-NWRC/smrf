#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_full_smrf
----------------------------------

Tests for an entire smrf run. The SMRF integration run!
"""

import unittest
import smrf
import os
from smrf.framework.model_framework import run_smrf
import numpy as np
from netCDF4 import Dataset

def compare_image(v_name,gold_dir,test_dir):
    """
    Compares two netcdfs images to and determines if they are the same.

    Args:
        v_name: Name with in the file contains
        gold_dir: Directory containing gold standard results
        test_dir: Directory containing test results to be compared
    Returns:
        Boolean: Whether the two images were the same
    """
    image1 = os.path.join(gold_dir,v_name+'.nc')
    image2 = os.path.join(test_dir,v_name+'.nc')

    d1 = Dataset(image1)
    gold = d1.variables[v_name][:]

    d2 = Dataset(image2)
    rough = d2.variables[v_name][:]
    result = np.abs(gold-rough)
    return  not np.any(result>0)

class TestRME(unittest.TestCase):
    """
    Integration test for SMRF using reynolds mountain east
    """

    def setUp(self):
        """
        Runs the simulation over reynolds_mountain_east
        """
        run_dir = os.path.abspath(os.path.join(os.path.dirname(smrf.__file__),
                                                '..','examples',
                                                'reynolds_mountain_east'))
        self.gold = os.path.abspath(os.path.join(os.path.dirname(smrf.__file__),
                                                '..','test_data',
                                                'reynolds_mountain_east','gold'))
        self.output = os.path.join(run_dir,'output')
        config = os.path.join(run_dir,'config.ini')
        run_smrf(config)

    def testAirTemp(self):
        """
        Compare that the air temperature is the same as the gold file provided.
        """
        a = compare_image('air_temp',self.gold,self.output)
        assert(a)

    def testDewPoint(self):
        """
        Compare that the dew point is the same as the gold file provided.
        """
        a = compare_image('dew_point',self.gold,self.output)
        assert(a)

    def testNetSolar(self):
        """
        Compare that the dew point is the same as the gold file provided.
        """
        a = compare_image('net_solar',self.gold,self.output)
        assert(a)

    def testPercentSnow(self):
        """
        Compare that the percent snow is the same as the gold file provided.
        """
        a = compare_image('percent_snow',self.gold,self.output)
        assert(a)

    def testPrecip(self):
        """
        Compare that the precip is the same as the gold file provided.
        """
        a = compare_image('precip',self.gold,self.output)
        assert(a)

    def testSnowDensity(self):
        """
        Compare that the dew point is the same as the gold file provided.
        """
        a = compare_image('snow_density',self.gold,self.output)
        assert(a)

    def testThermal(self):
        """
        Compare that the Thermal radiation is the same as the gold file provided.
        """
        a = compare_image('thermal',self.gold,self.output)
        assert(a)

    def testVaporPressure(self):
        """
        Compare that the vapor pressure is the same as the gold file provided.
        """
        a = compare_image('vapor_pressure',self.gold,self.output)
        assert(a)

    def testWindSpeed(self):
        """
        Compare that the wind speed is the same as the gold file provided.
        """
        a = compare_image('wind_speed',self.gold,self.output)
        assert(a)




if __name__ == '__main__':
    unittest.main()
