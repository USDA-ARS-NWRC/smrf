import numpy as np
import pandas as pd
import os
import netCDF4 as nc

from smrf.envphys.solar import toporad, irradiance
from tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestToporad(SMRFTestCaseLakes):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        date_time = pd.to_datetime('2/15/1990 20:30')
        cls.date_time = date_time.tz_localize('UTC')

        topo = nc.Dataset(os.path.join(cls.test_dir, 'topo/topo.nc'))
        topo.set_always_mask(False)
        cls.dem = topo.variables['dem'][:]
        topo.close()

    def test_elevrad(self):

        cosz = 0.45
        solar_irradiance = irradiance.direct_solar_irradiance(
            self.date_time, w=[0.28, 2.8])

        rad = toporad.Elevrad(
            self.dem,
            solar_irradiance,
            cosz)

        self.assertAlmostEqual(965.8825266529992, np.mean(rad.beam), places=4)
        self.assertAlmostEqual(943.726025997195, np.min(rad.beam), places=4)
        self.assertAlmostEqual(989.6426109567752, np.max(rad.beam), places=4)

        self.assertAlmostEqual(
            93.84312456169383, np.mean(rad.diffuse), places=4)
        self.assertAlmostEqual(
            87.84985436187131, np.min(rad.diffuse), places=4)
        self.assertAlmostEqual(
            99.39601061863907, np.max(rad.diffuse), places=4)

    def test_elevrad_options(self):

        cosz = 0.5
        tau_elevation = 80
        tau = 0.3
        omega = 0.55
        scattering_factor = 0.35
        surface_albedo = 0.3
        solar_irradiance = irradiance.direct_solar_irradiance(
            self.date_time, w=[0.28, 2.8])

        rad = toporad.Elevrad(
            self.dem,
            solar_irradiance,
            cosz,
            tau_elevation=tau_elevation,
            tau=tau,
            omega=omega,
            scattering_factor=scattering_factor,
            surface_albedo=surface_albedo)

        self.assertAlmostEqual(866.52075, np.mean(rad.beam), places=4)
        self.assertAlmostEqual(839.8351, np.min(rad.beam), places=4)
        self.assertAlmostEqual(895.3271, np.max(rad.beam), places=4)

        self.assertAlmostEqual(76.050644, np.mean(rad.diffuse), places=4)
        self.assertAlmostEqual(71.9361, np.min(rad.diffuse), places=4)
        self.assertAlmostEqual(79.77791, np.max(rad.diffuse), places=4)
