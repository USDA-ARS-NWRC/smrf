from copy import deepcopy
from inicheck.tools import cast_all_variables
from inicheck.utilities import pcfg
import unittest

from smrf.framework.model_framework import can_i_run_smrf

from tests.test_configurations import SMRFTestCase


class TestLoadData(SMRFTestCase):
    dist_variables = ['air_temp', 'vapor_pressure', 'wind', 'precip',
                      'cloud_factor', 'thermal']
    options = {'user': 'unittest_user',
               'password': 'WsyR4Gp9JlFee6HwOHAQ',
               'host': '10.200.28.137',
               'database': 'weather_db',
               'metadata': 'tbl_metadata',
               'data_table': 'tbl_level2',
               'station_table': 'tbl_stations',
               'air_temp': 'air_temp',
               'vapor_pressure': 'vapor_pressure',
               'precip': 'precip_accum',
               'solar': 'solar_radiation',
               'wind_speed': 'wind_speed',
               'wind_direction': 'wind_direction',
               'cloud_factor': 'cloud_factor',
               'port': '32768'
            }
    def can_i_run_smrf(self, config):
        """
        Test whether a config is possible to run
        """
        try:
            run_smrf(config)
            return True

        except Exception as e:
            return False

    def test_station_start_date(self):
        """
        Test the start date
        """

        # Test the start date
        config = deepcopy(self.base_config)
        # Use dates not in the dataset, expecting an error
        config.raw_cfg['time']['start_date'] = '2018-01-01 00:00'
        config.raw_cfg['time']['end_date'] = '2018-02-01 00:00'

        # apply the new recipies
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # test the base run with the config file
        self.assertFalse(self.can_i_run_smrf(config))

#     def test_station_end_date(self):
#         """
#         Test the end date
#         """
#
#         # test the end date
#         config = deepcopy(self.base_config)
#         config.raw_cfg['time']['end_date'] = '2018-02-01 00:00'
#
#         # apply the new recipies
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         # test the base run with the config file
#         result = can_i_run_smrf(config)
#         self.assertFalse(result)
#
#     def test_all_stations(self):
#         """
#         Test using all stations
#         """
#
#         # test the end date
#         config = deepcopy(self.base_config)
#         config.raw_cfg['stations']['stations'] = ['RMESP', 'RME_176']
#
#         # apply the new recipies
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         # test the base run with the config file
#         result = can_i_run_smrf(config)
#         self.assertFalse(result)
#
#
#     def test_mysql_data(self):
#         """
#         Use a simple user tester on the weather database to ensure loading is performed
#         correctly. This will not work outside of NWRC until we convert so SQLalchemy.
#         """
#
#         # test a succesful run specifiying stations
#         config = deepcopy(self.base_config)
#         config.raw_cfg['stations']['stations'] = ['RMESP', 'RME_176']
#         del config.raw_cfg['csv']
#         config.raw_cfg['mysql'] = self.options
#
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         result = can_i_run_smrf(config)
#         self.assertTrue(result)
#
#         # test a succesful run specifiying client
#         config = deepcopy(self.base_config)
#         config.raw_cfg['stations']['client'] = 'RME_test'
#         del config.raw_cfg['csv']
#         config.raw_cfg['mysql'] = self.options
#
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         result = can_i_run_smrf(config)
#         self.assertTrue(result)
#
#
#     def test_mysql_wrong_password(self):
#         """ wrong password to mysql """
#
#         config = deepcopy(self.base_config)
#         config.raw_cfg['stations']['stations'] = ['RMESP', 'RME_176']
#         del config.raw_cfg['csv']
#
#         # test wrong password
#         options = deepcopy(self.options)
#         options['password'] = 'not_the_right_password'
#         config.raw_cfg['mysql'] = options
#
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         result = can_i_run_smrf(config)
#         self.assertFalse(result)
#
#     def test_mysql_wrong_port(self):
#         """ test with wrong port to trigger different error """
#
#         config = deepcopy(self.base_config)
#         config.raw_cfg['stations']['stations'] = ['RMESP', 'RME_176']
#         del config.raw_cfg['csv']
#         options = deepcopy(self.options)
#         options['port'] = '123456'
#         config.raw_cfg['mysql'] = options
#
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         result = can_i_run_smrf(config)
#         self.assertFalse(result)
#
#     def test_mysql_metadata_error(self):
#         """ test no metadata found """
#
#         config = deepcopy(self.base_config)
#         config.raw_cfg['stations']['stations'] = ['NOT_STID', 'NOPE']
#         del config.raw_cfg['csv']
#         config.raw_cfg['mysql'] = deepcopy(self.options)
#
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         result = can_i_run_smrf(config)
#         self.assertFalse(result)
#
#     def test_mysql_data_error(self):
#         """ test no data found """
#
#         config = deepcopy(self.base_config)
#         config.raw_cfg['stations']['stations'] = ['RMESP', 'RME_176']
#         del config.raw_cfg['csv']
#         config.raw_cfg['mysql'] = deepcopy(self.options)
#
#         # wrong time
#         config.raw_cfg['time']['start_date'] = '2018-01-01 00:00'
#         config.raw_cfg['time']['end_date'] = '2018-02-01 00:00'
#
#         config.apply_recipes()
#         config = cast_all_variables(config, config.mcfg)
#
#         result = can_i_run_smrf(config)
#         self.assertFalse(result)

    #@unittest.skip(" Skipping over WRF test for issues with when to detrend")
    def test_grid_wrf(self):
        """ WRF NetCDF loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        wrf_grid = {'data_type': 'wrf',
                    'wrf_file': './RME/gridded/WRF_test.nc',
                    'zone_number': '11',
                    'zone_letter': 'N'}
        config.raw_cfg['gridded'] = wrf_grid
        config.raw_cfg['system']['threading'] = 'False'
        config.raw_cfg['system']['log_file'] = './log.txt'

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
             config.raw_cfg[v]['grid_mask'] = 'False'

        config.raw_cfg['precip']['station_adjust_for_undercatch'] = 'False'
        config.raw_cfg['thermal']['correct_cloud'] = 'False'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2015-03-03 00:00'
        config.raw_cfg['time']['end_date'] = '2015-03-03 04:00'
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        assert 'station_adjust_for_undercatch' not in config.cfg['precip'].keys()
        self.assertTrue(config.cfg['thermal']['correct_cloud'] == False)
        self.assertTrue(config.cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)

    #@unittest.skip(" Skipping over hrrr_local test for issues with weather_forecast_retrieval")
    def test_grid_hrrr(self):
        """ HRRR grib2 loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        hrrr_grid = {'data_type': 'hrrr_grib',
                    'hrrr_directory': './RME/gridded/hrrr_test/',
                    'zone_number': '11',
                    'zone_letter': 'N'}
        config.raw_cfg['gridded'] = hrrr_grid
        config.raw_cfg['system']['threading'] = 'False'

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.raw_cfg['precip']['station_adjust_for_undercatch'] = 'False'
        config.raw_cfg['thermal']['correct_cloud'] = 'True'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2018-07-22 16:00'
        config.raw_cfg['time']['end_date'] = '2018-07-22 20:00'

        config.raw_cfg['topo']['threading'] = 'False'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue('station_adjust_for_undercatch' not in config.cfg['precip'].keys())
        self.assertTrue(config.cfg['thermal']['correct_cloud'] == True)
        self.assertTrue(config.cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)

    #@unittest.skip(" Skipping over hrrr_local test for issues with weather_forecast_retrieval")
    def test_grid_hrrr_local(self):
        """ HRRR grib2 loading with local elevation gradient """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        hrrr_grid = {'data_type': 'hrrr_grib',
                    'hrrr_directory': './RME/gridded/hrrr_test/',
                    'zone_number': 11,
                    'zone_letter': 'N'}
        config.raw_cfg['gridded'] = hrrr_grid
        config.raw_cfg['system']['threading'] = 'False'
        config.raw_cfg['system']['log_file'] = None
        # config.raw_cfg['system']['timeout'] = 10

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        # local gradient
        config.raw_cfg['air_temp']['grid_local'] = 'True'
        config.raw_cfg['air_temp']['grid_local_n'] = '25' # only 47 grid cells

        config.raw_cfg['vapor_pressure']['grid_local'] = 'True'

        # Only 47 grid cells in domain
        config.raw_cfg['vapor_pressure']['grid_local_n'] = '25'
        config.raw_cfg['precip']['grid_local'] = 'True'
        config.raw_cfg['precip']['grid_local_n'] = '25'
        config.raw_cfg['thermal']['correct_cloud'] = 'True'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2018-07-22 16:00'
        config.raw_cfg['time']['end_date'] = '2018-07-22 20:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue('station_adjust_for_undercatch' not in config.cfg['precip'].keys())
        self.assertTrue(config.cfg['thermal']['correct_cloud'] == True)
        self.assertTrue(config.cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)

    def test_grid_netcdf(self):
        """ Generic NetCDF loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        generic_grid = {'data_type': 'netcdf',
                    'netcdf_file': './RME/gridded/netcdf_test.nc',
                    'zone_number': '11',
                    'zone_letter': 'N',
                    'air_temp': 'air_temp',
                    'vapor_pressure': 'vapor_pressure',
                    'precip': 'precip',
                    'wind_speed': 'wind_speed',
                    'wind_direction': 'wind_direction',
                    'thermal': 'thermal',
                    'cloud_factor': 'cloud_factor'}
        config.raw_cfg['gridded'] = generic_grid
        config.raw_cfg['system']['time_out'] = '10'
        config.raw_cfg['system']['queue_max_values'] = '1'
        config.raw_cfg['system']['threading'] = 'False' # Doesn't work with true

        # set the distrition to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        # TODO Delete me as it should not be needed
        # config.raw_cfg['precip']['station_adjust_for_undercatch'] = 'False'
        config.raw_cfg['thermal']['correct_cloud'] = 'False'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2015-03-03 00:00'
        config.raw_cfg['time']['end_date'] = '2015-03-03 04:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue('station_adjust_for_undercatch' not in config.cfg['precip'].keys())
        self.assertTrue(config.cfg['thermal']['correct_cloud'] == False)
        self.assertTrue(config.cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
