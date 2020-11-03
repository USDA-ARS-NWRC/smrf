import netCDF4 as nc
import numpy as np
import pytz

from smrf.data import Topo
from smrf.distribute.wind.wind_ninja import WindNinjaModel
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes
from smrf.utils import utils
from smrf.utils.utils import date_range


class TestWindNinja(SMRFTestCaseLakes):

    def setup_wind_ninja(self, config):
        """Setup the wind ninja class

        Args:
            config (dict): config dict
        """

        # Load the topo
        topo = Topo(config['topo'])

        # Get the time steps correctly in the time zone
        tzinfo = pytz.timezone(config['time']['time_zone'])
        date_time = date_range(
            config['time']['start_date'],
            config['time']['end_date'],
            config['time']['time_step'],
            tzinfo)

        wn = WindNinjaModel(config)
        wn.initialize(topo, None)
        wn.initialize_interp(date_time[0])
        g_vel, g_ang = wn.convert_wind_ninja(date_time[0])

        return topo, wn, g_vel, g_ang

    def test_wind_ninja(self):

        config = self.base_config.cfg
        topo, wn, g_vel, g_ang = self.setup_wind_ninja(config)

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

    def test_wind_ninja_interpolation(self):

        config = self.base_config.cfg
        config['wind']['wind_ninja_dxdy'] = 50
        topo, wn, g_vel, g_ang = self.setup_wind_ninja(config)

        # The implied assumption is that this does not throw an
        # exception when running
        self.assertTrue(np.all(np.diff(wn.windninja_x) > 0))
        self.assertTrue(np.all(np.diff(wn.windninja_y) < 0))
        self.assertTrue(np.sum(np.isnan(g_vel)) == 0)
