#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_full_smrf
----------------------------------

Tests for an entire smrf run. The SMRF integration run!
"""

import unittest
import shutil
import smrf
import os
from smrf.framework.model_framework import can_i_run_smrf
from inicheck.tools import get_user_config, check_config, cast_all_variables
from copy import deepcopy
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

    d1 = Dataset(image1, 'r')
    gold = d1.variables[v_name][:]
    d1.close()

    d2 = Dataset(image2, 'r')
    rough = d2.variables[v_name][:]
    d2.close()

    result = np.abs(gold-rough)
    return  not np.any(result>0)

class TestRME(unittest.TestCase):
    """
    Integration test for SMRF using reynolds mountain east
    """
    @classmethod
    def setUpClass(self):
        """
        Runs the short simulation over reynolds mountain east
        """
        run_dir = os.path.abspath(os.path.join(os.path.dirname(smrf.__file__),
                                               '../tests',
					       'RME'))

        self.gold = os.path.abspath(os.path.join(os.path.dirname(smrf.__file__),
						'../tests',
                                                'RME',
                                                'gold'))


        self.output = os.path.join(run_dir,'output')

        # Remove any potential files to ensure fresh run
        if os.path.isdir(self.output):
            shutil.rmtree(self.output)

        config = os.path.join(run_dir,'config.ini')
        can_i_run_smrf(config)

    def testAirTemp(self):
        """
        Compare that the air temperature is the same as the gold file provided.
        """
        a = compare_image('air_temp',self.gold,self.output)
        assert(a)

    def testPrecipTemp(self):
        """
        Compare that the dew point is the same as the gold file provided.
        """
        a = compare_image('precip_temp',self.gold,self.output)
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


# class TestRMEHRRR(TestRME):
#     """
#     Integration test for SMRF using reynolds mountain east
#     """
#     @classmethod
#     def setUpClass(self):
#         """
#         Runs the short simulation over reynolds mountain east
#         """
#         run_dir = os.path.abspath(os.path.join(os.path.dirname(smrf.__file__),
#                                                '../tests',
# 					       'RME'))
#
#         self.gold = os.path.abspath(os.path.join(os.path.dirname(smrf.__file__),
# 						'../tests',
#                                                 'RME',
#                                                 'gold_hrrr'))
#
#
#         self.output = os.path.join(run_dir,'output')
#
#         #Remove any potential files to ensure fresh run
#         if os.path.isdir(self.output):
#             shutil.rmtree(self.output)
#
#         #################################################
#         # get the config file and set it up for this run
#         #################################################
#         config_file = 'test_base_config.ini'
#         if os.path.isfile(config_file):
#             self.test_dir = ''
#         elif os.path.isfile(os.path.join('tests', config_file)):
#             config_file = os.path.join('tests', config_file)
#             self.test_dir = 'tests'
#         else:
#             raise Exception('Configuration file not found for testing')
#
#         self.base_config = get_user_config(config_file, modules = 'smrf')
#         config = deepcopy(self.base_config)
#         del config.raw_cfg['csv']
#
#         hrrr_grid = {'data_type': 'hrrr',
#                     'directory': './RME/gridded/hrrr_test/',
#                     'zone_number': 11,
#                     'zone_letter': 'N'}
#         config.raw_cfg['gridded'] = hrrr_grid
#     #         config.raw_cfg['system']['max_values'] = 2
#         config.raw_cfg['system']['threading'] = False
#     #         config.raw_cfg['system']['timeout'] = 10
#
#         # set the distrition to grid, thermal defaults will be fine
#         variables = ['air_temp', 'vapor_pressure', 'wind', 'precip', 'solar', 'thermal']
#         for v in variables:
#             config.raw_cfg[v]['distribution'] = 'grid'
#             config.raw_cfg[v]['mask'] = False
#
#         # local gradient
#         config.raw_cfg['air_temp']['grid_local'] = True
#         config.raw_cfg['air_temp']['grid_local_n'] = 25 # only 47 grid cells
#
#         config.raw_cfg['vapor_pressure']['grid_local'] = True
#         config.raw_cfg['vapor_pressure']['grid_local_n'] = 25 # only 47 grid cells
#
#         config.raw_cfg['precip']['adjust_for_undercatch'] = False
#         config.raw_cfg['precip']['grid_local'] = True
#         config.raw_cfg['precip']['grid_local_n'] = 25
#         config.raw_cfg['thermal']['correct_cloud'] = True
#         config.raw_cfg['thermal']['correct_veg'] = True
#
#         # fix the time to that of the WRF_test.nc
#         config.raw_cfg['time']['start_date'] = '2018-07-22 16:00'
#         config.raw_cfg['time']['end_date'] = '2018-07-22 20:00'
#
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         # ensure that the recipes are used
#         self.assertTrue(config.raw_cfg['precip']['adjust_for_undercatch'] == False)
#         self.assertTrue(config.raw_cfg['thermal']['correct_cloud'] == True)
#         self.assertTrue(config.raw_cfg['thermal']['correct_veg'] == True)
#
#         can_i_run_smrf(config)

if __name__ == '__main__':
    unittest.main()
