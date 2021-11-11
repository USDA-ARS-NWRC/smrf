import unittest
import os, shutil
from inicheck.tools import get_user_config, check_config, cast_all_variables
from copy import deepcopy

from smrf.framework.model_framework import can_i_run_smrf, SMRF
from smrf.distribute.albedo import albedo


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
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)


class SMRFTestCaseLakes(unittest.TestCase):
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
        cls.base_config = get_user_config(cls.config_file, modules = 'smrf')

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


class TestConfigPermutations(unittest.TestCase):

    def setUp(self) -> None:
        config_file = os.path.join(
            os.path.dirname(__file__), "test_base_config.ini"
        )
        self.base_config = get_user_config(config_file, modules='smrf')

    def test_albedo_veg_unknown_values(self):
        config_updates = {
            "start_decay": ['1998-01-12'],
            "end_decay": ['1998-07-01'],
            "decay_method": ["date_method"],
            "veg_1000": ["0.2"]
        }
        base_config = deepcopy(self.base_config)
        base_config.raw_cfg["albedo"].update(config_updates)

        base_config.apply_recipes()
        test_config = cast_all_variables(base_config, base_config.mcfg)

        warnings, errors = check_config(test_config)
        self.assertTrue(len(errors) == 0)

        # the issue is that we parse this as ['0.2']
        self.assertEqual(test_config.cfg["albedo"]["veg_1000"], ['0.2'])
        smrf_obj = SMRF(test_config)
        albedo_obj = albedo(smrf_obj.ucfg.cfg["albedo"])

        # show that we parsed the unknown values correctly in albedo section
        self.assertEqual(0.2, albedo_obj.veg["1000"])
        # default values still come in correctly
        self.assertEqual(0.36, albedo_obj.veg["41"])
