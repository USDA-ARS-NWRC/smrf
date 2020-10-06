import os

import netCDF4 as nc
import numpy as np

from smrf import __version__
from smrf.framework.model_framework import SMRF
from smrf.output.output_netcdf import OutputNetcdf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestOutputNetCDF(SMRFTestCase):

    def setUp(self):
        super().setUpClass()
        self.smrf = SMRF(self.config_file)

        self.variable_dict = {
            'air_temp': {
                'variable': 'air_temp',
                'module': 'air_temp',
                'out_location': os.path.join(
                    self.smrf.config['output']['out_location'],
                    'air_temp'
                ),
                'info': {
                    'units': 'degree_Celsius',
                    'standard_name': 'air_temperature',
                    'long_name': 'Air temperature'
                }
            }
        }

    def test_netcdf_smrf_version(self):

        self.smrf.loadTopo()

        OutputNetcdf(
            self.variable_dict,
            self.smrf.topo,
            self.smrf.config['time'],
            self.smrf.config['output'])

        n = nc.Dataset(self.variable_dict['air_temp']['file_name'])
        version = n.getncattr('SMRF_version')
        self.assertTrue(n.variables['air_temp'].dtype == np.float32)
        n.close()

        self.assertEqual(__version__, version)

    def test_netcdf_precision(self):
        self.smrf.config['output']['netcdf_output_precision'] = 'double'

        self.smrf.loadTopo()

        OutputNetcdf(
            self.variable_dict,
            self.smrf.topo,
            self.smrf.config['time'],
            self.smrf.config['output'])

        n = nc.Dataset(self.variable_dict['air_temp']['file_name'])
        self.assertTrue(n.variables['air_temp'].dtype == np.float64)
        n.close()
