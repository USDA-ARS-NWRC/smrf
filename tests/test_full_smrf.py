
import unittest
import os
from glob import glob
from inicheck.tools import get_user_config, check_config, cast_all_variables
from copy import deepcopy
import numpy as np
from netCDF4 import Dataset

from smrf.framework.model_framework import can_i_run_smrf
from tests.test_configurations import SMRFTestCase


class TestRME(SMRFTestCase):
    """
    Integration test for SMRF using reynolds mountain east
    """

    def compare_gold(self, out_dir):
        """
        Compare the model results with the gold standard
        
        Args:
            out_dir: the output directory for the model run
        """

        s = os.path.join(self.test_dir, out_dir, '*.nc')
        file_names = glob(os.path.realpath(s))

        # path to the gold standard
        gold_path = os.path.realpath(os.path.join(self.test_dir, 'RME', 'gold'))

        for file_name in file_names:
            nc_name = file_name.split('/')[-1]
            gold_file = os.path.join(gold_path, nc_name)
            print('Comparing {}'.format(nc_name))
            
            self.compare_netcdf_files(gold_file, file_name, atol=0)


    def testStationDataRun(self):
        """
        Test the standard station data run
        """
        result = can_i_run_smrf(self.config_file)
        self.assertTrue(result)

        self.compare_gold(os.path.join('RME', 'output'))

