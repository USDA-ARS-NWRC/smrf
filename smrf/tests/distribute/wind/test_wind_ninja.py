from datetime import timedelta

import netCDF4 as nc
import numpy as np
import pytz

from smrf.data import loadTopo
from smrf.data.mysql_data import date_range
from smrf.distribute.wind.wind_ninja import WindNinjaModel
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes
from smrf.utils import utils


class TestWindNinja(SMRFTestCaseLakes):

    def test_wind_ninja(self):
        """Test the wind ninja functions
        """

        config = self.base_config.cfg

        # Load the topo
        topo = loadTopo.Topo(config['topo'])

        # Get the time steps correctly in the time zone
        d = date_range(
            config['time']['start_date'],
            config['time']['end_date'],
            timedelta(minutes=int(config['time']['time_step'])))

        tzinfo = pytz.timezone(config['time']['time_zone'])
        date_time = [di.replace(tzinfo=tzinfo) for di in d]

        wn = WindNinjaModel(config)
        wn.initialize(topo, None)
        wn.initialize_interp(date_time[0])
        g_vel, g_ang = wn.convert_wind_ninja(date_time[0])

        # The x values are ascending
        self.assertTrue(np.all(np.diff(wn.windninja_x) > 0))

        # The y values are descnding
        self.assertTrue(np.all(np.diff(wn.windninja_y) < 0))

        # compare against gold
        g_vel = utils.set_min_max(
            g_vel, wn.config['min'], wn.config['max'])

        # check against gold
        # The two are not exactly the same as there is some float
        # precision error with netcdf
        n = nc.Dataset(self.gold_dir.joinpath('wind_speed.nc'))
        np.testing.assert_allclose(
            n.variables['wind_speed'][0, :],
            g_vel
        )
        n.close()

        n = nc.Dataset(self.gold_dir.joinpath('wind_direction.nc'))
        np.testing.assert_allclose(
            n.variables['wind_direction'][0, :],
            g_ang
        )
        n.close()
