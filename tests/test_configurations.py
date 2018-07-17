import unittest
from inicheck.tools import get_user_config, check_config

from smrf.framework.model_framework import run_smrf


class TestConfigurations(unittest.TestCase):
    """
    Test multiple configuration options to ensure that the all desired
    combinations work as expected.
    """

    def setUp(self):
        """
        Runs the short simulation over reynolds mountain east
        """
        
        # read in the base configuration
        self.base_config = get_user_config('test_base_config.ini', modules = 'smrf')
        
        

    def test_base_run(self):
        """
        Test the config for running configurations with different options
        """
        
        # test the base run with the config file
        result = run_smrf('test_base_config.ini')
        self.assertTrue(result)
        
        # test the base run with the config file
        result = run_smrf(self.base_config)
        self.assertTrue(result)