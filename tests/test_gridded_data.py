from copy import deepcopy
from inicheck.tools import cast_all_variables
from inicheck.utilities import pcfg
import unittest

from smrf.framework.model_framework import can_i_run_smrf

from tests.test_configurations import SMRFTestCase


class TestGriddedData(SMRFTestCase):

    def test_grid_wrf(self):
        """ WRF NetCDF loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        wrf_grid = {'data_type': 'wrf',
                    'file': './RME/gridded/WRF_test.nc',
                    'zone_number': 11,
                    'zone_letter': 'N'}
        config.raw_cfg['gridded'] = wrf_grid
        config.raw_cfg['system']['threading'] = False

        # set the distrition to grid, thermal defaults will be fine
        variables = ['air_temp', 'vapor_pressure', 'wind', 'precip', 'solar', 'thermal']
        for v in variables:
             config.raw_cfg[v]['mask'] = False

        config.raw_cfg['precip']['adjust_for_undercatch'] = False
        config.raw_cfg['thermal']['correct_cloud'] = False
        config.raw_cfg['thermal']['correct_veg'] = True

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2015-03-03 00:00'
        config.raw_cfg['time']['end_date'] = '2015-03-03 04:00'
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)


        # ensure that the recipes are used
        self.assertTrue(config.raw_cfg['precip']['adjust_for_undercatch'] == False)
        self.assertTrue(config.raw_cfg['thermal']['correct_cloud'] == False)
        self.assertTrue(config.raw_cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)


    def test_grid_hrrr(self):
        """ HRRR grib2 loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        hrrr_grid = {'data_type': 'hrrr',
                    'directory': './RME/gridded/hrrr_test/',
                    'zone_number': 11,
                    'zone_letter': 'N'}
        config.raw_cfg['gridded'] = hrrr_grid
        config.raw_cfg['system']['threading'] = False

        # set the distrition to grid, thermal defaults will be fine
        variables = ['air_temp', 'vapor_pressure', 'wind', 'precip', 'solar', 'thermal']
        for v in variables:
            config.raw_cfg[v]['mask'] = False

        config.raw_cfg['precip']['adjust_for_undercatch'] = False
        config.raw_cfg['thermal']['correct_cloud'] = True
        config.raw_cfg['thermal']['correct_veg'] = True

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2018-07-22 16:00'
        config.raw_cfg['time']['end_date'] = '2018-07-22 20:00'

        config.raw_cfg['topo']['threading'] = False

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(config.raw_cfg['precip']['adjust_for_undercatch'] == False)
        self.assertTrue(config.raw_cfg['thermal']['correct_cloud'] == True)
        self.assertTrue(config.raw_cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)


    def test_grid_hrrr_local(self):
        """ HRRR grib2 loading with local elevation gradient """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        hrrr_grid = {'data_type': 'hrrr',
                    'directory': './RME/gridded/hrrr_test/',
                    'zone_number': 11,
                    'zone_letter': 'N'}
        config.raw_cfg['gridded'] = hrrr_grid
        config.raw_cfg['system']['threading'] = False

        # set the distrition to grid, thermal defaults will be fine
        variables = ['air_temp', 'vapor_pressure', 'wind', 'precip', 'solar', 'thermal']
        for v in variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['mask'] = False

        # local gradient
        config.raw_cfg['air_temp']['grid_local'] = True
        config.raw_cfg['air_temp']['grid_local_n'] = 25 # only 47 grid cells

        config.raw_cfg['vapor_pressure']['grid_local'] = True
        config.raw_cfg['vapor_pressure']['grid_local_n'] = 25 # only 47 grid cells

        config.raw_cfg['precip']['adjust_for_undercatch'] = False
        config.raw_cfg['precip']['grid_local'] = True
        config.raw_cfg['precip']['grid_local_n'] = 25
        config.raw_cfg['thermal']['correct_cloud'] = True
        config.raw_cfg['thermal']['correct_veg'] = True

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2018-07-22 16:00'
        config.raw_cfg['time']['end_date'] = '2018-07-22 20:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(config.raw_cfg['precip']['adjust_for_undercatch'] == False)
        self.assertTrue(config.raw_cfg['thermal']['correct_cloud'] == True)
        self.assertTrue(config.raw_cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)


    def test_grid_netcdf(self):
        """ Generic NetCDF loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        wrf_grid = {'data_type': 'netcdf',
                    'file': './RME/gridded/netcdf_test.nc',
                    'zone_number': 11,
                    'zone_letter': 'N',
                    'air_temp': 'air_temp',
                    'vapor_pressure': 'vapor_pressure',
                    'precip': 'precip',
                    'wind_speed': 'wind_speed',
                    'wind_direction': 'wind_direction',
                    'thermal': 'thermal',
                    'cloud_factor': 'cloud_factor'}
        config.raw_cfg['gridded'] = wrf_grid
        config.raw_cfg['system']['time_out'] = 10
        config.raw_cfg['system']['max_values'] = 1
        config.raw_cfg['system']['threading'] = False # Doesn't work with true

        # set the distrition to grid, thermal defaults will be fine
        variables = ['air_temp', 'vapor_pressure', 'wind', 'precip', 'solar', 'thermal']
        for v in variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['mask'] = False

        config.raw_cfg['precip']['adjust_for_undercatch'] = False
        config.raw_cfg['thermal']['correct_cloud'] = False
        config.raw_cfg['thermal']['correct_veg'] = True

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2015-03-03 00:00'
        config.raw_cfg['time']['end_date'] = '2015-03-03 04:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(config.raw_cfg['precip']['adjust_for_undercatch'] == False)
        self.assertTrue(config.raw_cfg['thermal']['correct_cloud'] == False)
        self.assertTrue(config.raw_cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)


    def test_grid_hrrr_netcdf(self):
        """ HRRR netcdf opendap loading """

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        hrrr_grid = {'data_type': 'hrrr_netcdf',
                    'hrrr_opendap_url': 'http://10.200.28.72/thredds/catalog/hrrr_netcdf/catalog.xml',
                    'zone_number': 11,
                    'zone_letter': 'N'}

        config.raw_cfg['gridded'] = hrrr_grid
        config.raw_cfg['system']['threading'] = False

        # set the distrition to grid, thermal defaults will be fine
        variables = ['air_temp', 'vapor_pressure', 'wind', 'precip', 'solar', 'thermal']
        for v in variables:
            config.raw_cfg[v]['mask'] = False

        config.raw_cfg['precip']['adjust_for_undercatch'] = False
        config.raw_cfg['thermal']['correct_cloud'] = True
        config.raw_cfg['thermal']['correct_veg'] = True

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2018-07-22 16:00'
        config.raw_cfg['time']['end_date'] = '2018-07-22 20:00'

        config.raw_cfg['topo']['threading'] = False

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(config.raw_cfg['precip']['adjust_for_undercatch'] == False)
        self.assertTrue(config.raw_cfg['thermal']['correct_cloud'] == True)
        self.assertTrue(config.raw_cfg['thermal']['correct_veg'] == True)

        result = can_i_run_smrf(config)
        self.assertTrue(result)

