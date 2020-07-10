import os

from smrf.tests.smrf_test_case import SMRFTestCase


class SMRFTestCaseLakes(SMRFTestCase):
    """
    Runs the short simulation over Lakes.
    """

    basin_dir = SMRFTestCase.test_dir.joinpath('basins', 'Lakes')
    config_file = os.path.join(basin_dir, 'config.ini')
    gold_dir = basin_dir.joinpath('gold_hrrr')

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
                'storm_total',
                'last_storm_day_basin'
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
