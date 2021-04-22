import os

import numpy as np
import pandas as pd
from topocalc.shade import shade

from smrf.data import Topo
from smrf.envphys.albedo import albedo
from smrf.envphys.solar import irradiance, toporad
from smrf.envphys.sunang import sunang
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestToporad(SMRFTestCaseLakes):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        date_time = pd.to_datetime('2/15/1990 20:30')
        cls.date_time = date_time.tz_localize('UTC')

        cls.tau_elevation = 100.0
        cls.tau = 0.2
        cls.omega = 0.85
        cls.scattering_factor = 0.3
        cls.surface_albedo = 0.5
        cls.solar_irradiance = irradiance.direct_solar_irradiance(
            cls.date_time, w=[0.28, 2.8])

        topo_config = {
            'filename': os.path.join(cls.basin_dir, 'topo/topo.nc'),
            'northern_hemisphere': True,
            'gradient_method': 'gradient_d8',
            'sky_view_factor_angles': 72
        }
        cls.topo = Topo(topo_config)
        cls.dem = cls.topo.dem

        # inputs for toporad and stoporad
        cls.cosz, cls.azimuth, rad_vec = sunang(
            cls.date_time,
            cls.topo.basin_lat,
            cls.topo.basin_long)

        cls.elevrad = toporad.Elevrad(
            cls.dem,
            cls.solar_irradiance,
            cls.cosz)

        cls.illum_ang = shade(
            cls.topo.sin_slope,
            cls.topo.aspect,
            cls.azimuth,
            cls.cosz)

    def test_elevrad(self):

        rad = toporad.Elevrad(
            self.dem,
            self.solar_irradiance,
            cosz=0.45)

        np.testing.assert_allclose(965, np.mean(rad.beam), atol=1)
        np.testing.assert_allclose(943, np.min(rad.beam), atol=1)
        np.testing.assert_allclose(989, np.max(rad.beam), atol=1)

        np.testing.assert_allclose(93, np.mean(rad.diffuse), atol=1)
        np.testing.assert_allclose(87, np.min(rad.diffuse), atol=1)
        np.testing.assert_allclose(99, np.max(rad.diffuse), atol=1)

    def test_elevrad_options(self):

        rad = toporad.Elevrad(
            self.dem,
            self.solar_irradiance,
            cosz=0.5,
            tau_elevation=80,
            tau=0.3,
            omega=0.55,
            scattering_factor=0.35,
            surface_albedo=0.3)

        np.testing.assert_allclose(866, np.mean(rad.beam), atol=1)
        np.testing.assert_allclose(839, np.min(rad.beam), atol=1)
        np.testing.assert_allclose(895, np.max(rad.beam), atol=1)

        np.testing.assert_allclose(76, np.mean(rad.diffuse), atol=1)
        np.testing.assert_allclose(71, np.min(rad.diffuse), atol=1)
        np.testing.assert_allclose(79, np.max(rad.diffuse), atol=1)

    def test_toporad(self):

        trad_beam, trad_diffuse = toporad.toporad(
            self.elevrad.beam,
            self.elevrad.diffuse,
            self.illum_ang,
            self.topo.sky_view_factor,
            self.topo.terrain_config_factor,
            self.cosz,
            surface_albedo=0.5)

        np.testing.assert_allclose(706, np.mean(trad_beam), atol=1)
        np.testing.assert_allclose(85, np.min(trad_beam), atol=1)
        np.testing.assert_allclose(1162, np.max(trad_beam), atol=1)

        np.testing.assert_allclose(112, np.mean(trad_diffuse), atol=1)
        np.testing.assert_allclose(85, np.min(trad_diffuse), atol=1)
        np.testing.assert_allclose(148, np.max(trad_diffuse), atol=1)

    def test_stoporad_visible(self):

        alb_vis, alb_ir = albedo(
            20 * np.ones_like(self.dem), self.illum_ang, 500, 2000)

        srad_beam, srad_diffuse = toporad.stoporad(
            self.date_time,
            self.topo,
            self.cosz,
            self.azimuth,
            self.illum_ang,
            alb_vis,
            wavelength_range=[0.28, 0.7],
            tau_elevation=self.tau_elevation,
            tau=self.tau,
            omega=self.omega,
            scattering_factor=self.scattering_factor)

        np.testing.assert_allclose(350, np.mean(srad_beam), atol=1)
        np.testing.assert_allclose(49, np.min(srad_beam), atol=1)
        np.testing.assert_allclose(569, np.max(srad_beam), atol=1)

        np.testing.assert_allclose(66, np.mean(srad_diffuse), atol=1)
        np.testing.assert_allclose(49, np.min(srad_diffuse), atol=1)
        np.testing.assert_allclose(102, np.max(srad_diffuse), atol=1)

    def test_stoporad_ir(self):

        alb_vis, alb_ir = albedo(
            20 * np.ones_like(self.dem), self.illum_ang, 500, 2000)

        srad_beam, srad_diffuse = toporad.stoporad(
            self.date_time,
            self.topo,
            self.cosz,
            self.azimuth,
            self.illum_ang,
            alb_ir,
            wavelength_range=[0.7, 2.8],
            tau_elevation=self.tau_elevation,
            tau=self.tau,
            omega=self.omega,
            scattering_factor=self.scattering_factor)

        np.testing.assert_allclose(365, np.mean(srad_beam), atol=1)
        np.testing.assert_allclose(41, np.min(srad_beam), atol=1)
        np.testing.assert_allclose(602, np.max(srad_beam), atol=1)

        np.testing.assert_allclose(56, np.mean(srad_diffuse), atol=1)
        np.testing.assert_allclose(41, np.min(srad_diffuse), atol=1)
        np.testing.assert_allclose(71, np.max(srad_diffuse), atol=1)
