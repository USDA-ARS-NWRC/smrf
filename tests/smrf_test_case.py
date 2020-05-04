import os
import shutil
import unittest

import netCDF4 as nc
import numpy as np
from inicheck.tools import get_user_config

import smrf
from smrf.framework.model_framework import run_smrf


class SMRFTestCase(unittest.TestCase):
    """
    The base test case for SMRF that will load in the configuration file and store as
    the base config. Also will remove the output directory upon tear down.
    """
    dist_variables = [
        'air_temp',
        'cloud_factor',
        'precip',
        'thermal',
        'vapor_pressure',
        'wind',
    ]

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
        the values are exact
        """

        # open the gold and compare
        gold = nc.Dataset(gold_file)
        test = nc.Dataset(test_file)

        # compare the time first
        self.assertEqual(len(gold.variables['time']), len(
            test.variables['time']))

        # go through all variables and compare everything including
        # the attributes and data
        for var_name, v in gold.variables.items():

            # compare the dimensions
            for att in gold.variables[var_name].ncattrs():
                self.assertEqual(
                    getattr(gold.variables[var_name], att),
                    getattr(test.variables[var_name], att))

            # only compare those that are floats
            if gold.variables[var_name].datatype != np.dtype('S1'):
                error_msg = "Variable: {0} did not match gold standard".\
                    format(var_name)
                if os.getenv('NOT_ON_GOLD_HOST') is None:
                    np.testing.assert_array_equal(
                        test.variables[var_name][:],
                        gold.variables[var_name][:],
                        err_msg=error_msg
                    )
                else:
                    np.testing.assert_almost_equal(
                        test.variables[var_name][:],
                        gold.variables[var_name][:],
                        decimal=3,
                        err_msg=error_msg
                    )

        gold.close()
        test.close()

    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """
        base = os.path.dirname(smrf.__file__)
        cls.test_dir = os.path.abspath(os.path.join(base, '../', 'tests'))

        config_file = 'test_base_config.ini'
        config_file = os.path.join(cls.test_dir, config_file)

        if not os.path.isfile(config_file):
            raise Exception('Configuration file not found for testing')

        cls.config_file = config_file

        # read in the base configuration
        cls.base_config = get_user_config(config_file, modules='smrf')

    def tearDown(self):
        """
        Clean up the output directory
        """
        folder = os.path.join(self.base_config.cfg['output']['out_location'])
        if os.path.exists(folder):
            shutil.rmtree(folder)


class SMRFTestCaseLakes(SMRFTestCase):
    """
    The base test case for SMRF that will load in the configuration file and store as
    the base config. Also will remove the output directory upon tear down.
    """

    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """

        cls.test_dir = os.path.join('tests', 'Lakes')

        # check whether or not this is being ran as a single test or part of the suite
        cls.config_file = os.path.join(cls.test_dir, 'config.ini')

        # read in the base configuration
        cls.base_config = get_user_config(cls.config_file, modules='smrf')

        cls.gold = os.path.abspath(os.path.join(cls.test_dir, 'gold_hrrr'))
        cls.output = os.path.join(cls.test_dir, 'output')

        # Remove any potential files to ensure fresh run
        if os.path.isdir(cls.output):
            shutil.rmtree(cls.output)

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the output directory
        """
        folder = os.path.join(cls.base_config.cfg['output']['out_location'])
        if os.path.exists(folder):
            shutil.rmtree(folder)


#    def tearDown(self):
#        """
#        Clean up the output directory
#        """
#
#        folder = os.path.join(self.test_dir, 'output')
#        for the_file in os.listdir(folder):
#            file_path = os.path.join(folder, the_file)
#            try:
#                if os.path.isfile(file_path):
#                    os.unlink(file_path)
#                elif os.path.isdir(file_path): shutil.rmtree(file_path)
#            except Exception as e:
#                print(e)
