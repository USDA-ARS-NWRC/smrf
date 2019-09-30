from copy import deepcopy
import unittest
import pandas as pd
import numpy as np

from smrf.envphys import radiation
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
        lat = 34.416667
        lon = -119.9
        cosz = 0.6806311288888297
        zenith = 47.107
        az = -5.416396416371043
        
        # result = radiation.sunang(date_time, lat, lon)
        # self.assertTrue(result[0] == cosz)
        # self.assertTrue(result[1] == az)

        result = radiation.pysolar_sunang(date_time, lat, lon)
        self.assertTrue(result[0] == cosz)
        self.assertTrue(result[1] == az)


    # The code that generated the figures in the PR for comparison
    # between the IPW version and the Pysolar version
    # def test_sunang_timeseries(self):
    #     """ Sunang calculation timeseries """ 

    #     # RME basin lat/lon
    #     lon = -116.7547
    #     lat = 43.067

    #     date_time = pd.date_range('2015-10-01 00:00', '2016-09-30 00:00', freq='H', tz='UTC')
        
    #     df = pd.DataFrame(
    #         index=date_time,
    #         columns=['ipw_cosz', 'ipw_az', 'pysolar_cosz', 'pysolar_az']
    #         )

    #     for dt in date_time:
    #         print(dt)
    #         result = radiation.sunang(dt, lat, lon)
    #         df.loc[dt, ['ipw_cosz', 'ipw_az']] = result

    #         result = radiation.pysolar_sunang(dt, lat, lon)
    #         df.loc[dt, ['pysolar_cosz', 'pysolar_az']] = result

    #     df['zen_diff'] = (df['ipw_cosz'] - df['pysolar_cosz']) * 180 / np.pi
    #     df['az_diff'] = df['ipw_az'] - df['pysolar_az']

    #     df.to_csv('sunang_comparison.csv')

    #     ax = df['zen_diff'].hist(bins=50)
    #     ax.set_title('IPW zenith - Pysolar zenith')
    #     ax.set_xlabel('Zenith difference, degrees')
        
    #     ax = df['az_diff'].hist(bins=50)
    #     ax.set_title('IPW azimuth - Pysolar azimuth')
    #     ax.set_xlabel('Azimuth difference, degrees')
        
