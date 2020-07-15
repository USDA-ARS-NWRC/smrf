from copy import deepcopy

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestLoadNetcdf(SMRFTestCase):

    def test_grid_netcdf(self):

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        generic_grid = {
            'data_type': 'netcdf',
            'netcdf_file': './gridded/netcdf_test.nc',
            'air_temp': 'air_temp',
            'vapor_pressure': 'vapor_pressure',
            'precip': 'precip',
            'wind_speed': 'wind_speed',
            'wind_direction': 'wind_direction',
            'cloud_factor': 'cloud_factor'
        }
        config.raw_cfg['gridded'] = generic_grid
        config.raw_cfg['system']['time_out'] = '25'
        config.raw_cfg['system']['queue_max_values'] = '2'
        # Doesn't work with true
        config.raw_cfg['system']['threading'] = 'False'

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.raw_cfg['thermal']['correct_cloud'] = 'False'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        config.raw_cfg['wind']['wind_model'] = 'interp'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2015-03-03 00:00'
        config.raw_cfg['time']['end_date'] = '2015-03-03 04:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys())
        self.assertFalse(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        run_smrf(config)
