import unittest
import os, shutil
from inicheck.tools import get_user_config, check_config

from smrf.framework.model_framework import run_smrf


class SMRFTestCase(unittest.TestCase):
    """
    The base test case for SMRF that will load in the configuration file and store as
    the base config. Also will remove the output directory upon tear down.
    """

    def setUp(self):
        """
        Runs the short simulation over reynolds mountain east
        """
        
        # check whether or not this is being ran as a single test or part of the suite
        if os.path.isfile('test_base_config.ini'):
            config_file = 'test_base_config.ini'
            self.test_dir = ''
        elif os.path.isfile(os.path.join('tests', 'test_base_config.ini')):
            config_file = os.path.join('tests', 'test_base_config.ini')
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
        result = run_smrf(self.config_file)
        self.assertTrue(result)
        
        # test the base run with the config file
        result = run_smrf(self.base_config)
        self.assertTrue(result)
        
        