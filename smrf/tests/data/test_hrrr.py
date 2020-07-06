import os
from copy import deepcopy
from glob import glob

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestLoadGrid(SMRFTestCase):

    def compare_hrrr_gold(self, out_dir):
        """
        Compare the model results with the gold standard

        Args:
            out_dir: the output directory for the model run
        """

        output_dir = os.path.abspath(os.path.join(self.test_dir, out_dir))
        s = os.path.join(output_dir, '*.nc')
        file_names = glob(os.path.realpath(s))

        # path to the gold standard
        gold_path = os.path.realpath(
            os.path.join(self.test_dir, 'RME', 'gold_hrrr'))

        for file_name in file_names:
            nc_name = file_name.split('/')[-1]
            gold_file = os.path.join(gold_path, nc_name)

            self.compare_netcdf_files(gold_file, file_name)

    def test_grid_hrrr_local(self):
        """ HRRR grib2 loading with local elevation gradient """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        adj_config = {
            'gridded': {
                'data_type': 'hrrr_grib',
                'hrrr_directory': './RME/gridded/hrrr_test/',
            },
            'time': {
                'start_date': '2018-07-22 16:00',
                'end_date': '2018-07-22 20:00',
                'time_zone': 'utc'
            },
            'system': {
                'threading': False,
                'log_file': './RME/output/test.log'
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
        for v in self.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys())
        self.assertTrue(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        run_smrf(config)

        self.compare_hrrr_gold(config.raw_cfg['output']['out_location'][0])
