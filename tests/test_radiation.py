from copy import deepcopy
import unittest
import pandas as pd
import numpy as np
import utm

from smrf.data import loadTopo
from smrf.envphys import radiation, sunang
from tests.test_configurations import SMRFTestCase

class TestRadiation(SMRFTestCase):

    def test_sunang(self):
        """ Sunang calculation """

        # replicate the sun angle calculation from the sunang man page
        # for Santa Barbara on Feb 15, 1990 at 20:30 UTC
        # 
        #           | IPW       
        # zenith    | 47.122    
        # cosz      | 0.680436
        # azimuth   | -5.413
        #
        # The differences between the IPW version and python version
        # are insignificant and are only different because of the
        # values are pulled from stdout for IPW which uses printf

        date_time = pd.to_datetime('2/15/1990 20:30')
        date_time = date_time.tz_localize('UTC')
        lat = 34.4166667 # 35d, 25m, 0s
        lon = -119.9
        ipw_cosz = 0.680436
        ipw_azimuth = -5.413
        ipw_rad_vector = 0.98787
        
        result = radiation.sunang(date_time, lat, lon)
        self.assertTrue(result[0] == ipw_cosz)
        self.assertTrue(result[1] == ipw_azimuth)

        # try out the python version
        result = sunang.sunang(date_time, lat, lon)
        self.assertTrue(result[0], ipw_cosz)
        self.assertTrue(result[1], ipw_azimuth)
        self.assertTrue(result[2], ipw_rad_vector)

    
    def test_sunang_functions(self):
        """ Sunang functions """

        self.assertTrue(sunang.leapyear(2016))
        self.assertFalse(sunang.leapyear(2013))

        self.assertEqual(sunang.yearday(2016, 1, 31), 31)
        self.assertEqual(sunang.yearday(2016, 12, 31), 366)
        self.assertEqual(sunang.yearday(2015, 12, 31), 365)
        self.assertEqual(sunang.yearday(2015, 10, 1), 274)
        self.assertEqual(sunang.yearday(2016, 10, 1), 275)

        # replicating the IPW sunang example
        date_time = pd.to_datetime('2/15/1990 20:30')
        date_time = date_time.tz_localize('UTC')
        declin, omega, r = sunang.ephemeris(date_time)
        self.assertEqual(round(declin, 9), -0.218992538)
        self.assertEqual(round(omega, 9), -2.163529935)
        self.assertEqual(round(r, 9), 0.987871247)

    
    def test_sunang_array(self):
        """ Sunang as a numpy array """

        date_time = pd.to_datetime('2/15/1990 20:30')
        date_time = date_time.tz_localize('UTC')

        topo_config = {
            'basin_lon': -116.7547,
            'basin_lat': 43.067,
            'filename': 'tests/RME/topo/topo.nc',
            'type': 'netcdf',
            'threading': False
        }
        topo = loadTopo.topo(topo_config, calcInput=False, tempDir='tests/RME/output')

        # convert from UTM to lat/long
        lat, lon = utm.to_latlon(topo.X[0,0], topo.Y[0,0], 11, 'N')
        lat = np.nan * np.zeros_like(topo.X)
        lon = np.nan * np.zeros_like(topo.X)
        for idx, x in np.ndenumerate(topo.X):
            lat[idx], lon[idx] = utm.to_latlon(topo.X[idx], topo.Y[idx], 11, 'N')

        self.assertFalse(np.any(np.isnan(lat)))
        self.assertFalse(np.any(np.isnan(lon)))

        cosz, azimuth, rad_vec = sunang.sunang(date_time, lat, lon)
        
        self.assertTrue(isinstance(cosz, np.ndarray))
        self.assertTrue(isinstance(azimuth, np.ndarray))
        self.assertTrue(isinstance(rad_vec, float))


    # # The code that generated the figures in the PR for comparison
    # # between the IPW version and the Pysolar version
    # def test_sunang_timeseries(self):
    #     """ Sunang calculation timeseries """ 

    #     # RME basin lat/lon
    #     lon = -116.7547
    #     lat = 43.067

    #     date_time = pd.date_range('2015-10-01 00:00', '2016-09-30 00:00', freq='H', tz='UTC')
        
    #     df = pd.DataFrame(
    #         index=date_time,
    #         columns=['ipw_cosz', 'ipw_az', 'py_cosz', 'py_az']
    #         )

    #     for dt in date_time:
    #         print(dt)
    #         result = radiation.sunang(dt, lat, lon)
    #         df.loc[dt, ['ipw_cosz', 'ipw_az']] = result

    #         presult = sunang.sunang(dt, lat, lon)
    #         # df.loc[dt, ['py_cosz', 'py_az']] = [round(presult[0], 6), round(presult[1], 3)]
    #         df.loc[dt, ['py_cosz', 'py_az']] = presult[0:2]

    #     df['zen_diff'] = (df['ipw_cosz'] - df['py_cosz']) * 180 / np.pi
    #     df['az_diff'] = df['ipw_az'] - df['py_az']

    #     df.to_csv('sunang_comparison.csv')

    #     ax = df['zen_diff'].hist(bins=50)
    #     ax.set_title('IPW zenith - Python zenith')
    #     ax.set_xlabel('Zenith difference, degrees')
        
    #     ax = df['az_diff'].hist(bins=50)
    #     ax.set_title('IPW azimuth - Python azimuth')
    #     ax.set_xlabel('Azimuth difference, degrees')

        
