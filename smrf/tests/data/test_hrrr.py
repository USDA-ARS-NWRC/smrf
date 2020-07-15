from copy import deepcopy

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestLoadHRRR(SMRFTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        config = cls.base_config_copy()
        del config.raw_cfg['csv']

        adj_config = {
            'gridded': {
                'data_type': 'hrrr_grib',
                'hrrr_directory': './gridded/hrrr_test/',
            },
            'time': {
                'start_date': '2018-07-22 16:00',
                'end_date': '2018-07-22 20:00',
                'time_zone': 'utc'
            },
            'system': {
                'threading': False,
                'log_file': './output/test.log'
            },
            'air_temp': {
                'grid_local': True,
                'grid_local_n': 25
            },
            'vapor_pressure': {
                'grid_local': True,
                'grid_local_n': 25
            },
            'precip': {
                'grid_local': True,
                'grid_local_n': 25,
                'precip_temp_method': 'dew_point'
            },
            'wind': {
                'wind_model': 'interp'
            },
            'thermal': {
                'correct_cloud': True,
                'correct_veg': True
            },
            'albedo': {
                'grain_size': 300.0,
                'max_grain': 2000.0
            }
        }
        config.raw_cfg.update(adj_config)

        # set the distribution to grid, thermal defaults will be fine
        for v in cls.DIST_VARIABLES:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        cls.config = config
        cls.gold_dir = cls.basin_dir.joinpath('gold_hrrr')

    def test_grid_hrrr_local(self):

        run_smrf(self.config)
        self.compare_hrrr_gold()

    def test_load_timestep(self):

        config = deepcopy(self.config)
        config.raw_cfg['gridded']['hrrr_load_method'] = 'timestep'
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        run_smrf(config)

        self.compare_hrrr_gold()

    def test_load_timestep_threaded(self):

        config = deepcopy(self.config)
        config.raw_cfg['gridded']['hrrr_load_method'] = 'timestep'
        config.raw_cfg['system']['threading'] = True
        config.raw_cfg['system']['queue_max_values'] = 1
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        run_smrf(config)

        self.compare_hrrr_gold()
