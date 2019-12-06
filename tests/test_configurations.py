import unittest
import os
import shutil
from inicheck.tools import get_user_config, check_config
import netCDF4 as nc
import numpy as np

from smrf.framework.model_framework import run_smrf, can_i_run_smrf
import smrf


class SMRFTestCase(unittest.TestCase):
    """
    The base test case for SMRF that will load in the configuration file and store as
    the base config. Also will remove the output directory upon tear down.
    """
    dist_variables = ['air_temp', 'vapor_pressure', 'wind', 'precip',
                      'cloud_factor', 'thermal']

    def can_i_run_smrf(self, config):
        """
        Test whether a config is possible to run
        """
        try:
            run_smrf(config)
            return True

        except Exception as e:
            # print(e)
            return False

    def compare_netcdf_files(self, gold_file, test_file):
        """
        Compare two netcdf files to ensure that they are identical. The
        tests will compare the attributes of each variable and ensure that
        the values are within a 1e-8 tolerance (from `np.allclose`)
        """

        # open the gold and compare
        gold = nc.Dataset(gold_file)
        test = nc.Dataset(test_file)

        # compare the time first
        self.assertEqual(len(gold.variables['time']), len(
            test.variables['time']))

        # go through all variables and compare everything including the attributes and data
        for var_name, v in gold.variables.items():

            # compare the dimensions
            for att in gold.variables[var_name].ncattrs():
                self.assertEqual(
                    getattr(gold.variables[var_name], att),
                    getattr(test.variables[var_name], att))

            # only compare those that are floats
            if gold.variables[var_name].datatype != np.dtype('S1'):
                result = np.abs(
                    gold.variables[var_name][:] - test.variables[var_name][:])
                self.assertTrue(not np.any(result > 0))
                # self.assertTrue(np.allclose(gold.variables[var_name][:], test.variables[var_name][:], atol=atol))

        gold.close()
        test.close()

    def setUp(self):
        """
        Runs the short simulation over reynolds mountain east
        """

        # check whether or not this is being ran as a single test or part of the suite
        base = os.path.dirname(smrf.__file__)
        self.test_dir = os.path.join(base, '../', 'tests')

        config_file = 'test_base_config.ini'
        config_file = os.path.join(self.test_dir, config_file)

        if not os.path.isfile(config_file):
            raise Exception('Configuration file not found for testing')

        self.config_file = config_file

        # read in the base configuration
        self.base_config = get_user_config(config_file, modules='smrf')

    def tearDown(self):
        """
        Clean up the output directory
        """
        folder = os.path.join(self.base_config.cfg['output']['out_location'])
        shutil.rmtree(folder)


class TestConfigurations(SMRFTestCase):

    def test_base_run(self):
        """
        Test the config for running configurations with different options
        """
        # test the base run with the config file
        result = can_i_run_smrf(self.config_file)
        self.assertTrue(result)
