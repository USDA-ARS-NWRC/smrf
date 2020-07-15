from smrf.framework.model_framework import SMRF
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestThreading(SMRFTestCaseLakes):
    """
    Test for all defined BASE_THREAD_VARIABLES, not accounting for config
    dependent additions.
    """

    def test_multi_thread_variables(self):
        config = self.thread_config()
        smrf = SMRF(config)
        smrf.loadTopo()
        smrf.create_distribution()

        self.assertCountEqual(
            smrf.distribute['air_temp'].thread_variables,
            ['air_temp']
        )

        self.assertCountEqual(
            smrf.distribute['vapor_pressure'].thread_variables,
            ['vapor_pressure', 'dew_point', 'precip_temp']
        )

        self.assertCountEqual(
            smrf.distribute['wind'].thread_variables,
            ['wind_speed', 'wind_direction']
        )

        self.assertCountEqual(
            smrf.distribute['precipitation'].thread_variables,
            [
                'precip',
                'percent_snow',
                'snow_density',
                'storm_days',
                'storm_total'
            ]
        )

        self.assertCountEqual(
            smrf.distribute['albedo'].thread_variables,
            ['albedo_vis', 'albedo_ir']
        )

        self.assertCountEqual(
            smrf.distribute['cloud_factor'].thread_variables,
            ['cloud_factor']
        )

        self.assertCountEqual(
            smrf.distribute['solar'].thread_variables,
            [
                'cloud_ir_beam', 'net_solar', 'cloud_vis_beam',
                'clear_ir_diffuse', 'veg_vis_diffuse', 'clear_ir_beam',
                'cloud_ir_diffuse', 'clear_vis_diffuse', 'veg_ir_diffuse',
                'veg_vis_beam', 'clear_vis_beam', 'veg_ir_beam',
                'cloud_vis_diffuse'
            ]
        )

        self.assertCountEqual(
            smrf.distribute['thermal'].thread_variables,
            ['thermal', 'thermal_clear']
        )

        self.assertCountEqual(
            smrf.distribute['soil_temp'].thread_variables,
            []
        )

        if hasattr(self, 'threads'):
            self.assertTrue(len(smrf.threads == 12))
