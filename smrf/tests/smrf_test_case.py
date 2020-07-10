import os
import shutil
import unittest
from copy import deepcopy
from pathlib import PurePath

import netCDF4 as nc
import numpy as np
from inicheck.tools import get_user_config

import smrf
from smrf.framework.model_framework import run_smrf


class SMRFTestCase(unittest.TestCase):
    """
    The base test case for SMRF that will load in the configuration file
    and store as the base config. Also will remove the output
    directory upon tear down.

    Runs the short simulation over reynolds mountain east
    """
    DIST_VARIABLES = frozenset([
        'air_temp',
        'cloud_factor',
        'precip',
        'thermal',
        'vapor_pressure',
        'wind',
    ])

    BASE_INI_FILE_NAME = 'config.ini'

    test_dir = PurePath(smrf.__file__).parent.joinpath('tests')
    basin_dir = test_dir.joinpath('basins', 'RME')
    config_file = os.path.join(basin_dir, BASE_INI_FILE_NAME)

    @property
    def dist_variables(self):
        if self._dist_variables is None:
            self._dist_variables = list(self.DIST_VARIABLES)
        return self._dist_variables

    @property
    def base_config(self):
        return deepcopy(self._base_config)

    @classmethod
    def base_config_copy(cls):
        return deepcopy(cls._base_config)

    @classmethod
    def load_base_config(cls):
        cls._base_config = get_user_config(cls.config_file, modules='smrf')

    @classmethod
    def setUpClass(cls):
        cls.load_base_config()
        cls.create_output_dir()

    @classmethod
    def tearDownClass(cls):
        cls.remove_output_dir()
        delattr(cls, 'output_dir')

    @classmethod
    def create_output_dir(cls):
        folder = os.path.join(cls._base_config.cfg['output']['out_location'])

        # Remove any potential files to ensure fresh run
        if os.path.isdir(folder):
            shutil.rmtree(folder)

        os.makedirs(folder)
        cls.output_dir = folder

    @classmethod
    def remove_output_dir(cls):
        if hasattr(cls, 'output_dir') and \
                os.path.exists(cls.output_dir):
            shutil.rmtree(cls.output_dir)

    @staticmethod
    def can_i_run_smrf(config):
        """
        Test whether a config is possible to run
        """
        try:
            run_smrf(config)
            return True

        except Exception as e:
            print(e)
            return False

    @staticmethod
    def assert_gold_equal(gold, not_gold, error_msg):
        """Compare two arrays

        Arguments:
            gold {array} -- gold array
            not_gold {array} -- not gold array
            error_msg {str} -- error message to display
        """

        if os.getenv('NOT_ON_GOLD_HOST') is None:
            np.testing.assert_array_equal(
                not_gold,
                gold,
                err_msg=error_msg
            )
        else:
            np.testing.assert_almost_equal(
                not_gold,
                gold,
                decimal=3,
                err_msg=error_msg
            )

    def setUp(self):
        self._dist_variables = None

    def compare_netcdf_files(self, gold_file, test_file):
        """
        Compare two netcdf files to ensure that they are identical. The
        tests will compare the attributes of each variable and ensure that
        the values are exact
        """

        gold = nc.Dataset(gold_file)
        test = nc.Dataset(test_file)

        np.testing.assert_equal(
            gold.variables['time'][:],
            test.variables['time'][:],
            err_msg="Time steps did not match: \nGOLD {0} \n TEST {1}".format(
                gold.variables['time'], test.variables['time']
            )
        )

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
                error_msg = "Variable: {0} did not match gold standard". \
                    format(var_name)
                self.assert_gold_equal(
                    gold.variables[var_name][:],
                    test.variables[var_name][:],
                    error_msg
                )

        gold.close()
        test.close()
