from datetime import timedelta

import pytz
from inicheck.tools import cast_all_variables, get_user_config

from smrf.distribute import wind
from smrf.data.mysql_data import date_range
from smrf.data import loadTopo

from tests.test_configurations import SMRFTestCaseLakes

class TestWind(SMRFTestCaseLakes):

    def test_wind_ninja(self):
        """Test the wind ninja functions
        """

        config = self.base_config.cfg

        # Load the topo
        topo = loadTopo.topo(config['topo'], calcInput=False,
                             tempDir='tests/Lakes/output')
        
        # Get the timesetps correctly in the time zone
        d = date_range(
            config['time']['start_date'],
            config['time']['end_date'],
            timedelta(minutes=int(config['time']['time_step'])))

        tzinfo = pytz.timezone(config['time']['time_zone'])
        date_time = [di.replace(tzinfo=tzinfo) for di in d]

        wn = wind.wind(config['wind'],
                        config['precip']['distribute_drifts'],
                        config)

        # meshgrid points
        wn.X = topo.X
        wn.Y = topo.Y
        
        wn.initialize_wind_ninja(topo)
        wn.convert_wind_ninja(date_time[0])
