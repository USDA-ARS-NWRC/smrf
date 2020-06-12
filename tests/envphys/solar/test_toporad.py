import numpy as np
import pandas as pd
import os

from topocalc.shade import shade

from smrf.data import loadTopo
from smrf.envphys.sunang import sunang
from smrf.envphys.solar import toporad, irradiance
from tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestToporad(SMRFTestCaseLakes):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        date_time = pd.to_datetime('2/15/1990 20:30')
        cls.date_time = date_time.tz_localize('UTC')

        cls.cosz = 0.45
        cls.solar_irradiance = irradiance.direct_solar_irradiance(
            cls.date_time, w=[0.28, 2.8])

        topo_config = {
            'filename': os.path.join(cls.test_dir, 'topo/topo.nc'),
            'northern_hemisphere': True,
            'gradient_method': 'gradient_d8',
            'sky_view_factor_angles': 72
        }
        cls.topo = loadTopo.Topo(
            topo_config,
            tempDir=os.path.join(cls.test_dir, 'output')
        )
        cls.dem = cls.topo.dem

    def test_elevrad(self):

        rad = toporad.Elevrad(
            self.dem,
            self.solar_irradiance,
            self.cosz)

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

        rad = toporad.Elevrad(
            self.dem,
            self.solar_irradiance,
            cosz,
            tau_elevation=tau_elevation,
            tau=tau,
            omega=omega,
            scattering_factor=scattering_factor,
            surface_albedo=surface_albedo)

        self.assertAlmostEqual(866.520786181747, np.mean(rad.beam), places=4)
        self.assertAlmostEqual(839.8351806768451, np.min(rad.beam), places=4)
        self.assertAlmostEqual(895.3270566804218, np.max(rad.beam), places=4)

        self.assertAlmostEqual(
            76.05066002013795, np.mean(rad.diffuse), places=4)
        self.assertAlmostEqual(
            71.93614207728453, np.min(rad.diffuse), places=4)
        self.assertAlmostEqual(
            79.77788947641184, np.max(rad.diffuse), places=4)

    def test_toporad(self):

        # inputs for toporad
        cosz, azimuth, rad_vec = sunang(
            self.date_time,
            self.topo.basin_lat,
            self.topo.basin_long)

        erad = toporad.Elevrad(
            self.dem,
            self.solar_irradiance,
            self.cosz)

        illum_ang = shade(
            self.topo.sin_slope,
            self.topo.aspect,
            azimuth,
            cosz)

        trad_beam, trad_diffuse = toporad.toporad(
            erad.beam,
            erad.diffuse,
            illum_ang,
            self.topo.sky_view_factor,
            self.topo.terrain_config_factor,
            cosz,
            surface_albedo=0.5)

        self.assertAlmostEqual(727.5828933374338, np.mean(trad_beam), places=4)
        self.assertAlmostEqual(80.36698468013624, np.min(trad_beam), places=4)
        self.assertAlmostEqual(1161.5784794841636, np.max(trad_beam), places=4)

        self.assertAlmostEqual(
            108.48478468598306, np.mean(trad_diffuse), places=4)
        self.assertAlmostEqual(
            72.89786165248275, np.min(trad_diffuse), places=4)
        self.assertAlmostEqual(
            195.75464273116648, np.max(trad_diffuse), places=4)
