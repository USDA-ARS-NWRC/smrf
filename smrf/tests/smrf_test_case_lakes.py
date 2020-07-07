import os
import shutil

from inicheck.tools import get_user_config

import smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class SMRFTestCaseLakes(SMRFTestCase):
    """
    The base test case for SMRF that will load in the configuration file
    and store as the base config. Also will remove the output directory
    upon tear down.
    """

    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """

        base = os.path.dirname(smrf.__file__)
        cls.test_dir = os.path.join(base, 'tests', 'Lakes')
        cls.config_file = os.path.join(cls.test_dir, 'config.ini')

        # read in the base configuration
        cls.base_config = get_user_config(cls.config_file, modules='smrf')

        cls.gold = os.path.abspath(os.path.join(cls.test_dir, 'gold_hrrr'))
        cls.output = os.path.join(cls.test_dir, 'output')

        # Remove any potential files to ensure fresh run
        if os.path.isdir(cls.output):
            shutil.rmtree(cls.output)

        # create the output dir
        os.makedirs(cls.output, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the output directory
        """
        folder = os.path.join(cls.base_config.cfg['output']['out_location'])
        if os.path.exists(folder):
            shutil.rmtree(folder)
