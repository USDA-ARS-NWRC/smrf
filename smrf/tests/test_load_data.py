#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_load_data
----------------------------------

Tests for `data.load_data` module.
"""

import unittest
from copy import deepcopy

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import can_i_run_smrf, run_smrf, SMRF
from smrf.tests.smrf_test_case import SMRFTestCase
from smrf.tests.utils.nwrc_check import NWRCCheck


@unittest.skipUnless(
    NWRCCheck.in_network(),
    "Skipping because we are not on the NWRC network"
)
class TestLoadMySQLData(SMRFTestCase):

    def test_mysql_data_w_stations(self):
        """
        Use a simple user tester on the weather database to ensure loading is
        performed correctly. This will not work outside of NWRC until we
        convert so SQLalchemy.
        """
        # test a successful run specifying stations
        config = self.base_config_copy()
        options = deepcopy(NWRCCheck.MYSQL_OPTIONS)
        config.raw_cfg['mysql'] = options

        config.raw_cfg['mysql']['stations'] = ['RMESP', 'RME_176']
        del config.raw_cfg['csv']

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        result = self.can_i_run_smrf(config)

        self.assertTrue(result)

    def test_mysql_data_w_client(self):
        """
        Run SMRF with MYSQL data from client, also can only be run from inside
        NWRC.
        """
        # test a successful run specifying client
        config = self.base_config_copy()
        options = deepcopy(NWRCCheck.MYSQL_OPTIONS)
        config.raw_cfg['mysql'] = options

        config.raw_cfg['mysql']['client'] = 'RME_test'
        del config.raw_cfg['csv']

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        result = can_i_run_smrf(config)
        assert result

    def test_mysql_metadata_error(self):
        """ test no metadata found """

        config = self.base_config_copy()
        options = deepcopy(NWRCCheck.MYSQL_OPTIONS)
        config.raw_cfg['mysql'] = options

        config.raw_cfg['mysql']['stations'] = ['NOT_STID', 'NOPE']
        del config.raw_cfg['csv']

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        with self.assertRaises(Exception):
            run_smrf(config)

    def test_mysql_data_error(self):
        """ test no data found """

        config = self.base_config_copy()
        options = deepcopy(NWRCCheck.MYSQL_OPTIONS)

        config.raw_cfg['mysql'] = options
        config.raw_cfg['mysql']['stations'] = ['RMESP', 'RME_176']
        del config.raw_cfg['csv']

        # wrong time
        config.raw_cfg['time']['start_date'] = '1900-01-01 00:00'
        config.raw_cfg['time']['end_date'] = '1900-02-01 00:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        with self.assertRaises(Exception):
            run_smrf(config)


class TestLoadCSVData(SMRFTestCase):

    def test_station_dates(self):
        """
        Test the start date not in the data
        """
        config = self.base_config_copy()

        # Use dates not in the dataset, expecting an error
        config.raw_cfg['time']['start_date'] = '1900-01-01 00:00'
        config.raw_cfg['time']['end_date'] = '1900-02-01 00:00'

        # apply the new recipes
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        with self.assertRaises(Exception):
            run_smrf(config)

    def test_all_stations(self):
        """
        Test using all stations
        """

        # test the end date
        config = self.base_config_copy()
        config.raw_cfg['csv']['stations'] = ['RMESP', 'RME_176']

        # apply the new recipies
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        self.assertIsInstance(run_smrf(config), SMRF)


if __name__ == '__main__':
    unittest.main()
