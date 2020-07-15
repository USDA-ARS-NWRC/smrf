from copy import deepcopy

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestLoadGrid(SMRFTestCase):

    def test_grid_wrf(self):
        """ WRF NetCDF loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        adj_config = {
            'gridded': {
                'data_type': 'wrf',
                'wrf_file': './gridded/WRF_test.nc',
            },
            'system': {
                'threading': 'False',
                'log_file': './output/log.txt'
            },
            'precip': {
                'station_adjust_for_undercatch': 'False'
            },
            'wind': {
                'wind_model': 'interp'
            },
            'thermal': {
                'correct_cloud': 'False',
                'correct_veg': 'True'
            },
            'time': {
                'start_date': '2015-03-03 00:00',
                'end_date': '2015-03-03 04:00'
            }
        }

        config.raw_cfg.update(adj_config)

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['grid_mask'] = 'False'

        # fix the time to that of the WRF_test.nc
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys()
        )
        self.assertFalse(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        run_smrf(config)
