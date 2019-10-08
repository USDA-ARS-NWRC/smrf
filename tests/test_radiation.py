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
        lat = 34.4166667  # 35d, 25m, 0s
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
        topo = loadTopo.topo(topo_config, calcInput=False,
                             tempDir='tests/RME/output')

        # convert from UTM to lat/long
        lat, lon = utm.to_latlon(topo.X[0, 0], topo.Y[0, 0], 11, 'N')
        lat = np.nan * np.zeros_like(topo.X)
        lon = np.nan * np.zeros_like(topo.X)
        for idx, x in np.ndenumerate(topo.X):
            lat[idx], lon[idx] = utm.to_latlon(
                topo.X[idx], topo.Y[idx], 11, 'N')

        self.assertFalse(np.any(np.isnan(lat)))
        self.assertFalse(np.any(np.isnan(lon)))

        cosz, azimuth, rad_vec = sunang.sunang(date_time, lat, lon)

        self.assertTrue(isinstance(cosz, np.ndarray))
        self.assertTrue(isinstance(azimuth, np.ndarray))
        self.assertTrue(isinstance(rad_vec, float))

    def test_solar(self):
        """ Test the solar function """

        # output from solar IPW function
        sin = 150.214

        # The example in solar
        date_time = pd.to_datetime('6/22/1990 00:00')
        date_time = date_time.tz_localize('UTC')

        # IPW version
        sipw = radiation.solar_ipw(date_time, w=[0.58, 0.68])
        self.assertTrue(sipw == sin)

        # Python version
        spy = radiation.solar(date_time, w=[0.58, 0.68])
        self.assertTrue(np.abs(spy - sin) <= 0.021)

    def test_twostream(self):
        """ Twostream calculation """

        # IPW command from man twostream is the first test
        # twostream -u 0.68 -t 0.2 -w 0.85 -g 0.3 -r 0.5 -s 159
        # twostream -u 0.05 -t 0.3 -w 0.8 -g 0.35 -r 0.6 -s 60
        # twostream -u 0.88 -t 0.2 -w 0.7 -g 0.3 -r 0.55 -s 1200

        # inputs
        cosz = [0.68, 0.05, 0.88]
        tau = [0.2, 0.3, 0.2]
        omega = [0.85, 0.8, 0.7]
        g = [0.3, 0.35, 0.3]
        R0 = [0.5, 0.6, 0.55]
        S0 = [159, 60, 1200]

        # outputs
        reflectance = [0.472814, 0.577519, 0.465302]
        transmittance = [0.912634, 0.365645, 0.912601]
        direct_transmittance = [0.745189, 0.00247875, 0.796703]
        upwelling_irradiance = [51.1207, 1.73256, 491.359]
        total_irradiance_at_bottom = [98.674, 1.09694, 963.707]
        direct_irradiance_normal_to_beam = [118.485, 0.148725, 956.044]

        for n in [0, 1]:

            # IPW way
            ipw_R = radiation.twostream_ipw(
                cosz[n], S0[n], tau=tau[n], omega=omega[n], g=g[n], R0=R0[n])
            self.assertTrue(ipw_R[0] == reflectance[n])
            self.assertTrue(ipw_R[1] == transmittance[n])
            self.assertTrue(ipw_R[2] == direct_transmittance[n])
            self.assertTrue(ipw_R[3] == upwelling_irradiance[n])
            self.assertTrue(ipw_R[4] == total_irradiance_at_bottom[n])
            self.assertTrue(ipw_R[5] == direct_irradiance_normal_to_beam[n])

            # Python way
            py_R = radiation.twostream(
                cosz[n], S0[n], tau=tau[n], omega=omega[n], g=g[n], R0=R0[n])

            # IPW is printed to %g format so convert
            for i, r in enumerate(py_R):
                py_R[i] = float('{:g}'.format(r))
            self.assertTrue(py_R[0] == reflectance[n])
            self.assertTrue(py_R[1] == transmittance[n])
            self.assertTrue(py_R[2] == direct_transmittance[n])
            self.assertTrue(py_R[3] == upwelling_irradiance[n])
            self.assertTrue(py_R[4] == total_irradiance_at_bottom[n])
            self.assertTrue(py_R[5] == direct_irradiance_normal_to_beam[n])

    def test_model_solar(self):
        """ Model solar radiation at a point """

        date_time = pd.to_datetime('2/15/1990 20:30')
        date_time = date_time.tz_localize('UTC')
        lat = 34.4166667  # 35d, 25m, 0s
        lon = -119.9
        tau = 0.2

        # IPW way
        ipw_cosz, ipw_az = radiation.sunang_ipw(date_time, lat, lon)
        ipw_sol = radiation.solar_ipw(date_time, [0.28, 2.8])
        ipw_R = radiation.twostream_ipw(ipw_cosz, ipw_sol, tau=tau)
        ipw_R[4]

        # Python way
        py_cosz, py_az, py_rad_vec = sunang.sunang(date_time, lat, lon)
        py_sol = radiation.solar(date_time, [0.28, 2.8])
        py_R = radiation.twostream(py_cosz, py_sol, tau=tau)

        py_R

    # def test_solar_timeseries(self):
    #     """ solar calculation timeseries """

    #     date_time = pd.date_range('2015-10-01 00:00', '2016-09-30 00:00', freq='H', tz='UTC')

    #     df = pd.DataFrame(
    #         index=date_time,
    #         columns=['solar_ipw', 'pysolar']
    #         )

    #     for dt in date_time:
    #         print(dt)
    #         result = radiation.solar_ipw(dt)
    #         df.loc[dt, 'solar_ipw'] = result

    #         presult = radiation.solar(dt)
    #         df.loc[dt, 'pysolar'] = presult

    #     df['solar_diff'] = df['solar_ipw'] - df['pysolar']

    #     df.to_csv('solar_comparison.csv')

    #     import matplotlib.pyplot as plt
    #     ax = df['solar_diff'].hist(bins=50)
    #     ax.set_title('IPW solar - Python solar')
    #     ax.set_xlabel('Difference exoatmospheric direct solar irradiance [W/m2]')
    #     plt.show()

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
