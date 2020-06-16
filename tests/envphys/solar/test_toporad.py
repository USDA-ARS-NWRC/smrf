import numpy as np
import pandas as pd
import os

from topocalc.shade import shade

from smrf.data import loadTopo
from smrf.envphys.sunang import sunang
from smrf.envphys.solar import toporad, irradiance
from smrf.envphys.albedo import albedo
from smrf.utils import utils
from tests.smrf_test_case_lakes import SMRFTestCaseLakes


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

    def setup(self):
        super().setup()

        self.assertTrue(self.tau_elevation == 100.0)
        self.assertTrue(self.tau == 0.2)
        self.assertTrue(self.omega == 0.85)
        self.assertTrue(self.scattering_factor == 0.3)
        self.assertTrue(self.surface_albedo == 0.5)

    def test_elevrad(self):

        rad = toporad.Elevrad(
            self.dem,
            self.solar_irradiance,
            cosz=0.45)

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

        rad = toporad.Elevrad(
            self.dem,
            self.solar_irradiance,
            cosz=0.5,
            tau_elevation=80,
            tau=0.3,
            omega=0.55,
            scattering_factor=0.35,
            surface_albedo=0.3)

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

        trad_beam, trad_diffuse = toporad.toporad(
            self.elevrad.beam,
            self.elevrad.diffuse,
            self.illum_ang,
            self.topo.sky_view_factor,
            self.topo.terrain_config_factor,
            self.cosz,
            surface_albedo=0.5)

        self.assertAlmostEqual(706.00646512025, np.mean(trad_beam), places=4)
        self.assertAlmostEqual(85.17261208557352, np.min(trad_beam), places=4)
        self.assertAlmostEqual(1164.002552980898, np.max(trad_beam), places=4)

        self.assertAlmostEqual(
            112.40386960667101, np.mean(trad_diffuse), places=4)
        self.assertAlmostEqual(
            84.87506304536915, np.min(trad_diffuse), places=4)
        self.assertAlmostEqual(
            148.25525747786014, np.max(trad_diffuse), places=4)

    def test_stoporad_ipw(self):

        wy_day, wyear = utils.water_day(self.date_time)
        tz_min_west = np.abs(self.date_time.utcoffset().total_seconds()/60)

        srad_beam, srad_diffuse = toporad.stoporad_ipw(
            self.date_time,
            self.tau_elevation,
            self.tau,
            self.omega,
            self.scattering_factor,
            wavelength_range=[0.28, 0.7],
            start=10.0,
            current_day=wy_day,
            time_zone=tz_min_west,
            year=wyear,
            cosz=self.cosz,
            azimuth=self.azimuth,
            grain_size=100,
            max_grain=700,
            dirt=2,
            topo=self.topo)

        self.assertAlmostEqual(
            351.25182444925485, np.mean(srad_beam), places=4)
        self.assertAlmostEqual(50.92724524244678, np.min(srad_beam), places=4)
        self.assertAlmostEqual(572.402983921415, np.max(srad_beam), places=4)

        self.assertAlmostEqual(
            66.89108278587302, np.mean(srad_diffuse), places=4)
        self.assertAlmostEqual(
            50.92724524244678, np.min(srad_diffuse), places=4)
        self.assertAlmostEqual(
            104.8765113187472, np.max(srad_diffuse), places=4)

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
            350.15499774108343, np.mean(srad_beam), places=4)
        self.assertAlmostEqual(49.93072201088423, np.min(srad_beam), places=4)
        self.assertAlmostEqual(570.8952497322141, np.max(srad_beam), places=4)

        self.assertAlmostEqual(
            65.79425607770162, np.mean(srad_diffuse), places=4)
        self.assertAlmostEqual(
            49.93072201088423, np.min(srad_diffuse), places=4)
        self.assertAlmostEqual(
            102.0245829059228, np.max(srad_diffuse), places=4)

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
            365.2325025385806, np.mean(srad_beam), places=4)
        self.assertAlmostEqual(41.89547121619991, np.min(srad_beam), places=4)
        self.assertAlmostEqual(602.1473403247246, np.max(srad_beam), places=4)

        self.assertAlmostEqual(
            56.30766430031142, np.mean(srad_diffuse), places=4)
        self.assertAlmostEqual(
            41.89547121619991, np.min(srad_diffuse), places=4)
        self.assertAlmostEqual(
            71.2741086202979, np.max(srad_diffuse), places=4)
