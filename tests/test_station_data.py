from copy import deepcopy
from inicheck.tools import cast_all_variables
from inicheck.utilities import pcfg
import unittest

from smrf.framework.model_framework import can_i_run_smrf

from tests.test_configurations import SMRFTestCase


class TestLoadData(SMRFTestCase):

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

#     def test_station_start_date(self):
#         """
#         Test the start date
#         """
#
#         # test the start date
#         config = deepcopy(self.base_config)
#         config.raw_cfg['time']['start_date'] = '2018-01-01 00:00'
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

