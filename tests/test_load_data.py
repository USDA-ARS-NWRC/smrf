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

from smrf.framework.model_framework import can_i_run_smrf, run_smrf
from tests.nwrc_check import NWRCCheck
from tests.smrf_test_case import SMRFTestCase


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
        config = deepcopy(self.base_config)
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
        config = deepcopy(self.base_config)
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

        config = deepcopy(self.base_config)
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

        config = deepcopy(self.base_config)
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
        config = deepcopy(self.base_config)

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
        config = deepcopy(self.base_config)
        config.raw_cfg['csv']['stations'] = ['RMESP', 'RME_176']

        # apply the new recipies
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        self.assertIsNone(run_smrf(config))


class TestLoadGrid(SMRFTestCase):

    def test_grid_wrf(self):
        """ WRF NetCDF loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        adj_config = {'gridded': {'data_type': 'wrf',
                                  'wrf_file': './RME/gridded/WRF_test.nc',
                                  'zone_number': '11',
                                  'zone_letter': 'N'},
                      'system': {'threading': 'False',
                                 'log_file': './output/log.txt'},
                      'precip': {'station_adjust_for_undercatch': 'False'},
                      'thermal': {'correct_cloud': 'False',
                                  'correct_veg': 'True'},
                      'time': {'start_date': '2015-03-03 00:00',
                               'end_date': '2015-03-03 04:00'}}

        config.raw_cfg.update(adj_config)

        # set the distribution to grid, thermal defaults will be fine
        for v in SMRFTestCase.dist_variables:
            config.raw_cfg[v]['grid_mask'] = 'False'

        # fix the time to that of the WRF_test.nc
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        assert 'station_adjust_for_undercatch' not in config.cfg['precip'].keys()
        self.assertFalse(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        self.assertIsNone(run_smrf(config))

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
        for v in SMRFTestCase.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.raw_cfg['precip']['station_adjust_for_undercatch'] = 'False'
        config.raw_cfg['thermal']['correct_cloud'] = 'True'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2018-07-22 16:00'
        config.raw_cfg['time']['end_date'] = '2018-07-22 20:00'

        #config.raw_cfg['system']['log_file'] = 'none'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        result = (
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys()
        )
        self.assertTrue(result)
        self.assertTrue(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        self.assertIsNone(run_smrf(config))

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
        config.raw_cfg['system']['log_file'] = './output/log.txt'

        # set the distribution to grid, thermal defaults will be fine
        for v in SMRFTestCase.dist_variables:
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
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys()
        )
        self.assertTrue(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        self.assertIsNone(run_smrf(config))

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
        config.raw_cfg['system']['time_out'] = '25'
        config.raw_cfg['system']['queue_max_values'] = '2'
        config.raw_cfg['system']['threading'] = 'False' # Doesn't work with true

        # set the distribution to grid, thermal defaults will be fine
        for v in SMRFTestCase.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.raw_cfg['thermal']['correct_cloud'] = 'False'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2015-03-03 00:00'
        config.raw_cfg['time']['end_date'] = '2015-03-03 04:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys()
        )
        self.assertFalse(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        self.assertIsNone(run_smrf(config))

class TestLoadTopo(SMRFTestCase):
    @classmethod
    def setUp(self):
        topo_config = {
            'filename': os.path.join(self.test_dir, 'RME/topo/topo.nc'),
            'northern_hemisphere':True,
        }

        self.topo = loadTopo.topo(
            topo_config,
            calcInput=False,
            tempDir=os.path.join(self.test_dir, 'RME/output')
        )

    def test_auto_calc_lat_lon(self):
        '''
        Test we calculate the basin lat long correctly
        '''

        self.assertTrue(self.topo.basin_lat)

if __name__ == '__main__':
    unittest.main()
