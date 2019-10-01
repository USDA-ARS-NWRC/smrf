from copy import deepcopy
import unittest
import pandas as pd
import numpy as np

from smrf.envphys import radiation, sunang
from tests.test_configurations import SMRFTestCase

from pysolar.solar import get_altitude, get_azimuth


class TestRadiation(SMRFTestCase):

    def test_sunang(self):
        """ Sunang calculation """

        # replicate the sun angle calculation from the sunang man page
        # for Santa Barbara on Feb 15, 1990 at 20:30 UTC
        # The difference between IPW sunang and Pysolar for the following
        # example are:
        #           | IPW       | PySolar
        # zenith    | 47.122    | 47.107
        # cosz      | 0.680436  | 0.680631
        # azimuth   | -5.413    | -5.416
        #
        # The differences for this one instance is hundredths of degrees
        # in zenith and thousandths in azimuth

        date_time = pd.to_datetime('2/15/1990 20:30')
        date_time = date_time.tz_localize('UTC')
        lat = 34.4166667 # 35d, 25m, 0s
        lon = -119.9
        ipw_cosz = 0.680436
        ipw_azimuth = -5.413
        ipw_rad_vector = 0.98787
        cosz = 0.6806311288888297
        zenith = 47.107
        az = -5.416396416371043
        
        result = radiation.sunang(date_time, lat, lon)
        self.assertTrue(result[0] == ipw_cosz)
        self.assertTrue(result[1] == ipw_azimuth)

        # try out the python version
        result = sunang.sunang(date_time, lat, lon)
        self.assertTrue(round(result[0], 6), ipw_cosz)
        self.assertTrue(round(result[1], 3), ipw_azimuth)
        self.assertTrue(round(result[2], 5), ipw_rad_vector)


        # result = radiation.pysolar_sunang(date_time, lat, lon)
        # self.assertTrue(result[0] == cosz)
        # self.assertTrue(result[1] == az)

    
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

        
