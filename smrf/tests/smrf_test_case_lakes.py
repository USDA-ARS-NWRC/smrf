import logging
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

        # clear the logger
        for handler in logging.root.handlers:
            logging.root.removeHandler(handler)

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the output directory
        """
        folder = os.path.join(cls.base_config.cfg['output']['out_location'])
        if os.path.exists(folder):
            shutil.rmtree(folder)

    def assert_list(self, list1, list2):
        """Couldn't get the assert_list to work"""

        self.assertTrue(sorted(list1) == sorted(list2))

    def assert_thread_variables(self):

        self.assert_list(
            self.smrf.distribute['air_temp'].thread_variables,
            ['air_temp']
        )

        self.assert_list(
            self.smrf.distribute['vapor_pressure'].thread_variables,
            ['vapor_pressure', 'dew_point', 'precip_temp']
        )

        self.assert_list(
            self.smrf.distribute['wind'].thread_variables,
            ['wind_speed', 'wind_direction']
        )

        self.assert_list(
            self.smrf.distribute['precipitation'].thread_variables,
            [
                'precip',
                'percent_snow',
                'snow_density',
                'storm_days',
                'storm_total'
            ]
        )

        self.assert_list(
            self.smrf.distribute['albedo'].thread_variables,
            ['albedo_vis', 'albedo_ir']
        )

        self.assert_list(
            self.smrf.distribute['cloud_factor'].thread_variables,
            ['cloud_factor']
        )

        self.assert_list(
            self.smrf.distribute['solar'].thread_variables,
            [
                'cloud_ir_beam', 'net_solar', 'cloud_vis_beam',
                'clear_ir_diffuse', 'veg_vis_diffuse', 'clear_ir_beam',
                'cloud_ir_diffuse', 'clear_vis_diffuse', 'veg_ir_diffuse',
                'veg_vis_beam', 'clear_vis_beam', 'veg_ir_beam',
                'cloud_vis_diffuse'
            ]
        )

        self.assert_list(
            self.smrf.distribute['thermal'].thread_variables,
            ['thermal', 'thermal_clear', 'thermal_veg', 'thermal_cloud']
        )

        self.assert_list(
            self.smrf.distribute['soil_temp'].thread_variables,
            []
        )

        if hasattr(self, 'threads'):
            self.assertTrue(len(self.smrf.threads == 12))
