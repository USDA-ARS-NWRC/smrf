#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_load_data
----------------------------------

Tests for `data.load_data` module.
"""


import unittest
import os
from glob import glob
from copy import deepcopy
import requests
from inicheck.tools import cast_all_variables
from inicheck.utilities import pcfg

from smrf.framework.model_framework import can_i_run_smrf, run_smrf
from tests.test_configurations import SMRFTestCase


def is_at_NWRC(url):
    """
    Checks that were on the NWRC network
    """

    try:
        r = requests.get(url)
        code = r.status_code

    except Exception as e:
        code = 404

    return code == 200


class TestLoadMySQLData(SMRFTestCase):

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

    url = 'http://' + options['host']
    on_network = is_at_NWRC(url)

    @unittest.skipIf(not on_network, "Skipping b/c we are not on the NWRC network")
    def test_mysql_data_w_stations(self):
        """
        Use a simple user tester on the weather database to ensure loading is
        performed correctly. This will not work outside of NWRC until we
        convert so SQLalchemy.
        """
        # test a successful run specifying stations
        config = deepcopy(self.base_config)
        options = deepcopy(self.options)
        config.raw_cfg['mysql'] = options

        config.raw_cfg['mysql']['stations'] = ['RMESP', 'RME_176']
        del config.raw_cfg['csv']

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        result = self.can_i_run_smrf(config)

        self.assertTrue(result)

    @unittest.skipIf(not on_network, "Skipping b/c we are not on the NWRC network")
    def test_mysql_data_w_client(self):
        """
        Run SMRF with MYSQL data from client, also can only be run from inside
        NWRC.
        """
        # test a succesful run specifiying client
        config = deepcopy(self.base_config)
        options = deepcopy(self.options)
        config.raw_cfg['mysql'] = options

        config.raw_cfg['mysql']['client'] = 'RME_test'
        del config.raw_cfg['csv']

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        result = can_i_run_smrf(config)
        assert result

    @unittest.skipIf(not on_network, "Skipping b/c we are not on the NWRC network")
    def test_mysql_metadata_error(self):
        """ test no metadata found """

        config = deepcopy(self.base_config)
        options = deepcopy(self.options)
        config.raw_cfg['mysql'] = options

        config.raw_cfg['mysql']['stations'] = ['NOT_STID', 'NOPE']
        del config.raw_cfg['csv']

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        with self.assertRaises(Exception):
            result = run_smrf(config)

    @unittest.skipIf(not on_network, "Skipping b/c we are not on the NWRC network")
    def test_mysql_data_error(self):
        """ test no data found """

        config = deepcopy(self.base_config)
        options = deepcopy(self.options)

        config.raw_cfg['mysql'] = options
        config.raw_cfg['mysql']['stations'] = ['RMESP', 'RME_176']
        del config.raw_cfg['csv']

        # wrong time
        config.raw_cfg['time']['start_date'] = '1900-01-01 00:00'
        config.raw_cfg['time']['end_date'] = '1900-02-01 00:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        with self.assertRaises(Exception):
            result = run_smrf(config)


class TestLoadCSVData(SMRFTestCase):

    def test_station_dates(self):
        """
        Test the start date not in the data
        """

        # Test the start date
        config = deepcopy(self.base_config)

        # Use dates not in the dataset, expecting an error
        config.raw_cfg['time']['start_date'] = '1900-01-01 00:00'
        config.raw_cfg['time']['end_date'] = '1900-02-01 00:00'

        # apply the new recipies
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        result = self.can_i_run_smrf(config)

        # test the base run with the config file
        self.assertFalse(result)

    def test_all_stations(self):
        """
        Test using all stations
        """

        # test the end date
        config = deepcopy(self.base_config)
        config.raw_cfg['csv']['stations'] = ['RMESP', 'RME_176']

        # apply the new recipies
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # test the base run with the config file
        result = self.can_i_run_smrf(config)
        assert result


if __name__ == '__main__':
    unittest.main()
