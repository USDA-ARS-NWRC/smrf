import os
import unittest

import netCDF4 as nc
import numpy as np

import smrf
from smrf.data import loadTopo


class TestLoadTopo(unittest.TestCase):
    @classmethod
    def setUp(self):
        base = os.path.dirname(smrf.__file__)
        self.test_dir = os.path.abspath(os.path.join(base, 'tests'))
        tempDir = os.path.join(self.test_dir, 'RME/output')

        if not os.path.exists(tempDir):
            os.mkdir(tempDir)

        topo_config = {
            'filename': os.path.join(self.test_dir, 'RME/topo/topo.nc'),
            'northern_hemisphere': True,
            'gradient_method': 'gradient_d8',
            'sky_view_factor_angles': 72
        }

        self.ds = nc.Dataset(topo_config['filename'])

        self.topo = loadTopo.Topo(
            topo_config,
            tempDir=tempDir
        )

    @classmethod
    def tearDown(self):
        self.ds.close()

    def test_center_calc_masked(self):
        '''
        Test the basin center calculation using the basin mask
        '''
        cx, cy = self.topo.get_center(self.ds, mask_name='mask')
        np.testing.assert_almost_equal(cx, 520033.7187500, 7)
        np.testing.assert_almost_equal(cy, 4768035.0, 7)

    def test_center_calc_domain(self):
        '''
        Test the basin center calculation for the entire basin domain
        '''
        cx, cy = self.topo.get_center(self.ds, mask_name=None)
        np.testing.assert_almost_equal(cx, 520050.0, 7)
        np.testing.assert_almost_equal(cy, 4768055.0, 7)

    def test_auto_calc_lat_lon(self):
        '''
        Test calculating the basin lat long correctly
        '''
        # Original RME
        # basin_lon:                     -116.7547
        # basin_lat:                     43.067
        np.testing.assert_almost_equal(
            self.topo.basin_lat, 43.06475372378507, 7)
        np.testing.assert_almost_equal(
            self.topo.basin_long, -116.75395420397061, 7)

    def test_projection_attributes(self):
        '''
        Confirm that this class has important projection attributes
        '''
        # Attribute directly used in load Grid as attributess from topo class
        important = ['basin_lat', 'basin_long', 'zone_number',
                     'northern_hemisphere']

        for at in important:
            self.assertTrue(hasattr(self.topo, at))
