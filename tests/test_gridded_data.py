from copy import deepcopy
from inicheck.tools import cast_all_variables
from inicheck.utilities import pcfg
import unittest
import urllib.request
from glob import glob
import os

from smrf.framework.model_framework import can_i_run_smrf

from tests.test_configurations import SMRFTestCase



class TestGriddedData(SMRFTestCase):

    def compare_hrrr_gold(self, out_dir):
        """
        Compare the model results with the gold standard
        
        Args:
            out_dir: the output directory for the model run
        """

        s = os.path.join(self.test_dir, out_dir, '*.nc')
        file_names = glob(os.path.realpath(s))

        # path to the gold standard
        gold_path = os.path.realpath(os.path.join(self.test_dir, 'RME', 'gold_hrrr'))

        for file_name in file_names:
            nc_name = file_name.split('/')[-1]
            gold_file = os.path.join(gold_path, nc_name)
            print('Comparing {}'.format(nc_name))

            if 'precip_temp' in nc_name:
                atol = 0.1 # because dew point uses a tolerance value for convergance
            elif 'thermal' in nc_name:
                atol = 0.5 # since thermal uses dew point
            elif 'wind_direction' in nc_name:
                atol = 0.1
            elif 'vapor_pressure' in nc_name:
                atol = 5 # since vapor_pressure uses dew point
            else:
                atol = 1e-3

            self.compare_netcdf_files(gold_file, file_name, atol=atol)


    def test_grid_wrf(self):
        """ WRF NetCDF loading """

        print('Test WRF NetCDF loading')
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


    def test_grid_netcdf(self):
        """ Generic NetCDF loading """

        print('Generic NetCDF loading')

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


    def test_grid_hrrr(self):
        """ HRRR grib2 loading """

        print('HRRR grib2 loading')
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

        # set some specific variable setting
        config.raw_cfg['air_temp']['grid_local'] = True
        config.raw_cfg['precip']['grid_local'] = True
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

        # compare with the gold
        self.compare_hrrr_gold(config.raw_cfg['output']['out_location'][0])

    def test_grid_hrrr_netcdf(self):
        """ HRRR netcdf opendap loading """

        print('HRRR netcdf opendap')

        url_path = 'http://10.200.28.71/thredds/catalog/hrrr_netcdf/catalog.xml'

        # check if we can access the THREDDS server
        try:
            status_code = urllib.request.urlopen(url_path).getcode()
            if status_code != 200:
                raise unittest.SkipTest('Unable to access THREDDS data server, skipping OpenDAP tests')
        except:
            raise unittest.SkipTest('Unable to access THREDDS data server, skipping OpenDAP tests')

        config = deepcopy(self.base_config)
        del config.raw_cfg['csv']

        hrrr_grid = {'data_type': 'hrrr_netcdf',
                    'hrrr_netcdf_opendap_url': url_path,
                    'zone_number': 11,
                    'zone_letter': 'N'}

        config.raw_cfg['gridded'] = hrrr_grid
        config.raw_cfg['system']['threading'] = False
        config.raw_cfg['logging']['log_file'] = None

        # set the distrition to grid, thermal defaults will be fine
        variables = ['air_temp', 'vapor_pressure', 'wind', 'precip', 'solar', 'thermal']
        for v in variables:
            config.raw_cfg[v]['mask'] = False

        # set some specific variable setting
        config.raw_cfg['air_temp']['grid_local'] = True
        config.raw_cfg['precip']['grid_local'] = True
        config.raw_cfg['precip']['adjust_for_undercatch'] = False
        config.raw_cfg['thermal']['correct_cloud'] = True
        config.raw_cfg['thermal']['correct_veg'] = True

        # fix the time to what we need for comparing with the gold
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

        # compare with the gold
        self.compare_hrrr_gold(config.raw_cfg['output']['out_location'][0])

