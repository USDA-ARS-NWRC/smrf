import numpy as np
import pandas as pd
import os

from topocalc.shade import shade

from smrf.data import loadTopo
from smrf.envphys.sunang import sunang
from smrf.envphys.solar import toporad, irradiance
from smrf.utils import utils
from tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestToporad(SMRFTestCaseLakes):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        date_time = pd.to_datetime('2/15/1990 20:30')
        cls.date_time = date_time.tz_localize('UTC')

        cls.tau_elevation = 100.0
        cls.tau = 0.2,
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

        self.assertAlmostEqual(803.7440367209555, np.mean(trad_beam), places=4)
        self.assertAlmostEqual(92.33279332519623, np.min(trad_beam), places=4)
        self.assertAlmostEqual(1271.850616069636, np.max(trad_beam), places=4)

        self.assertAlmostEqual(
            124.71739693920429, np.mean(trad_diffuse), places=4)
        self.assertAlmostEqual(
            84.2389981611408, np.min(trad_diffuse), places=4)
        self.assertAlmostEqual(
            217.9322245307723, np.max(trad_diffuse), places=4)

    def test_stoporad_ipw(self):

        wy_day, wyear = utils.water_day(self.date_time)
        tz_min_west = np.abs(self.date_time.utcoffset().total_seconds()/60)

        srad = toporad.stoporad_ipw(
            self.tau_elevation,
            self.tau,
            self.omega,
            self.scattering_factor,
            wavelength_range=[0.28, 0.7],
            start=10.0,
            current_day=wy_day,
            time_zone=tz_min_west,
            year=wyear,
            latitude=self.topo.basin_lat,
            longitude=self.topo.basin_long,
            cosz=self.cosz,
            azimuth=self.azimuth,
            grain_size=100,
            max_grain=700,
            dirt=2,
            solar_irradiance=self.solar_irradiance,
            topo=self.topo)

        srad
