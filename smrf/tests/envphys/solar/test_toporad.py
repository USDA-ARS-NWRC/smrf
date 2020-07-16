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

        self.assertAlmostEqual(965.8828575567114, np.mean(rad.beam), places=4)
        self.assertAlmostEqual(943.7263794826135, np.min(rad.beam), places=4)
        self.assertAlmostEqual(989.6429308508227, np.max(rad.beam), places=4)

        self.assertAlmostEqual(
            93.84315440085071, np.mean(rad.diffuse), places=4)
        self.assertAlmostEqual(
            87.84988698685561, np.min(rad.diffuse), places=4)
        self.assertAlmostEqual(
            99.39603484739534, np.max(rad.diffuse), places=4)

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

        self.assertAlmostEqual(866.5210770956645, np.mean(rad.beam), places=4)
        self.assertAlmostEqual(839.8354626316999, np.min(rad.beam), places=4)
        self.assertAlmostEqual(895.3273572653653, np.max(rad.beam), places=4)

        self.assertAlmostEqual(
            76.05068555235343, np.mean(rad.diffuse), places=4)
        self.assertAlmostEqual(
            71.93616622814766, np.min(rad.diffuse), places=4)
        self.assertAlmostEqual(
            79.77791625995671, np.max(rad.diffuse), places=4)

    def test_toporad(self):

        trad_beam, trad_diffuse = toporad.toporad(
            self.elevrad.beam,
            self.elevrad.diffuse,
            self.illum_ang,
            self.topo.sky_view_factor,
            self.topo.terrain_config_factor,
            self.cosz,
            surface_albedo=0.5)

        self.assertAlmostEqual(706.0067021452699, np.mean(trad_beam), places=4)
        self.assertAlmostEqual(85.17264068026927, np.min(trad_beam), places=4)
        self.assertAlmostEqual(1164.002943767303, np.max(trad_beam), places=4)

        self.assertAlmostEqual(
            112.40390734361924, np.mean(trad_diffuse), places=4)
        self.assertAlmostEqual(
            84.87509154016982, np.min(trad_diffuse), places=4)
        self.assertAlmostEqual(
            148.2553072510663, np.max(trad_diffuse), places=4)

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

        self.assertAlmostEqual(
            350.1547099434225, np.mean(srad_beam), places=4)
        self.assertAlmostEqual(49.930680972072594, np.min(srad_beam), places=4)
        self.assertAlmostEqual(570.8947805048191, np.max(srad_beam), places=4)

        self.assertAlmostEqual(
            65.79420200041265, np.mean(srad_diffuse), places=4)
        self.assertAlmostEqual(
            49.930680972072594, np.min(srad_diffuse), places=4)
        self.assertAlmostEqual(
            102.02449905038313, np.max(srad_diffuse), places=4)

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

        self.assertAlmostEqual(
            365.23243248652074, np.mean(srad_beam), places=4)
        self.assertAlmostEqual(41.8954631805951, np.min(srad_beam), places=4)
        self.assertAlmostEqual(602.1472248320969, np.max(srad_beam), places=4)

        self.assertAlmostEqual(
            56.30765350042961, np.mean(srad_diffuse), places=4)
        self.assertAlmostEqual(
            41.8954631805951, np.min(srad_diffuse), places=4)
        self.assertAlmostEqual(
            71.27409494983297, np.max(srad_diffuse), places=4)
