import os

import netCDF4 as nc

from smrf import __version__
from smrf.framework.model_framework import SMRF
from smrf.output.output_netcdf import OutputNetcdf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestOutputNetCDF(SMRFTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.smrf = SMRF(cls.config_file)

    def test_netcdf_smrf_version(self):

        variable_dict = {
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

        self.smrf.loadTopo()

        OutputNetcdf(
            variable_dict,
            self.smrf.topo,
            self.smrf.config['time'],
            self.smrf.config['output'])

        n = nc.Dataset(variable_dict['air_temp']['file_name'])
        version = n.getncattr('SMRF_version')
        n.close()

        self.assertEqual(__version__, version)
