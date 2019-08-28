import unittest
import os, shutil
from inicheck.tools import get_user_config, check_config
import netCDF4 as nc
import numpy as np

from smrf.framework.model_framework import can_i_run_smrf


class SMRFTestCase(unittest.TestCase):
    """
    The base test case for SMRF that will load in the configuration file and store as
    the base config. Also will remove the output directory upon tear down.
    """

    def compare_netcdf_files(self, gold_file, test_file, atol=1e-5):
        """
        Compare two netcdf files to ensure that they are identical. The
        tests will compare the attributes of each variable and ensure that
        the values are within a 1e-8 tolerance (from `np.allclose`)
        """

        # open the gold and compare
        gold = nc.Dataset(gold_file)
        test = nc.Dataset(test_file)

        # compare the time first
        self.assertEqual(len(gold.variables['time']), len(test.variables['time']))

        # go through all variables and compare everything including the attributes and data
        for var_name, v in gold.variables.items():
            
            # compare the dimensions
            for att in gold.variables[var_name].ncattrs():
                self.assertEqual(
                    getattr(gold.variables[var_name], att),
                    getattr(test.variables[var_name], att))

            # only compare those that are floats
            if gold.variables[var_name].datatype != np.dtype('S1'):
                self.assertTrue(np.allclose(gold.variables[var_name][:], test.variables[var_name][:], atol=atol))

        gold.close()
        test.close()

    def setUp(self):
        """
        Runs the short simulation over reynolds mountain east
        """

        # check whether or not this is being ran as a single test or part of the suite
        config_file = 'test_base_config.ini'
        if os.path.isfile(config_file):
            self.test_dir = ''
        elif os.path.isfile(os.path.join('tests', config_file)):
            config_file = os.path.join('tests', config_file)
            self.test_dir = 'tests'
        else:
            raise Exception('Configuration file not found for testing')

        self.config_file = config_file

        # read in the base configuration
        self.base_config = get_user_config(config_file, modules = 'smrf')

    def tearDown(self):
        """
        Clean up the output directory
        """

        folder = os.path.join(self.test_dir, 'RME', 'output')
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)



class TestConfigurations(SMRFTestCase):

    def test_base_run(self):
        """
        Test the config for running configurations with different options
        """

        # test the base run with the config file
        result = can_i_run_smrf(self.config_file)
        self.assertTrue(result)
#         self.assertTrue(False)

        # test the base run with the config file
        result = can_i_run_smrf(self.base_config)
        self.assertTrue(result)
