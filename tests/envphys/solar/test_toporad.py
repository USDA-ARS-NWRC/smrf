import numpy as np
import pandas as pd
import utm
import os
import netCDF4 as nc

from smrf.data import loadTopo
from smrf.envphys.solar import toporad, irradiance
from tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestToporad(SMRFTestCaseLakes):

    def test_elevrad(self):

        date_time = pd.to_datetime('2/15/1990 20:30')
        date_time = date_time.tz_localize('UTC')

        topo = nc.Dataset(os.path.join(self.test_dir, 'topo/topo.nc'))
        topo.set_always_mask(False)

        cosz = 0.45
        # tau_elevation = 100
        # tau = 0.2
        # omega = 0.85
        # scattering_factor = 0.3
        # surface_albedo = 0.5
        solar_irradiance = irradiance.direct_solar_irradiance(
            date_time, w=[0.28, 2.8])

        rad = toporad.Elevrad(
            topo.variables['dem'][:],
            solar_irradiance,
            cosz)

        rad.beam
