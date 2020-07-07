import logging

import pandas as pd
import numpy as np
from weather_forecast_retrieval.hrrr import HRRR

from smrf.envphys.vapor_pressure import rh2vp
from smrf.envphys.solar.cloud import get_hrrr_cloud


class LoadGribHRRR():

    VARIABLES = [
        'air_temp',
        'vapor_pressure',
        'precip',
        'wind_speed',
        'wind_direction',
        'cloud_factor'
    ]

    def __init__(self, *args, **kwargs):

        for keys in kwargs.keys():
            setattr(self, keys, kwargs[keys])

        self._logger = logging.getLogger(__name__)

        if self.config['hrrr_load_method'] == 'timestep':
            self.timestep_dates()

        self.hrrr = HRRR(external_logger=self._logger)

    def timestep_dates(self):
        self.end_date = self.start_date + pd.to_timedelta(20, 'minutes')

    def load(self):
        """
        Load the data from the High Resolution Rapid Refresh (HRRR) model
        The variables returned from the HRRR class in dataframes are

            - metadata
            - air_temp
            - relative_humidity
            - precip_int
            - cloud_factor
            - wind_u
            - wind_v

        The function will take the keys and load them into the appropriate
        objects within the `grid` class. The vapor pressure will be calculated
        from the `air_temp` and `relative_humidity`. The `wind_speed` and
        `wind_direction` will be calculated from `wind_u` and `wind_v`
        """

        self._logger.info('Reading data from from HRRR directory: {}'.format(
            self.config['hrrr_directory']
        ))

        metadata, data = self.hrrr.get_saved_data(
            self.start_date,
            self.end_date,
            self.bbox,
            output_dir=self.config['hrrr_directory'],
            force_zone_number=self.topo.zone_number
        )

        self.parse_data(metadata, data)

    def load_timestep(self, date_time):
        """Load a single time step for HRRR

        Args:
            date_time (datetime): date time to load
        """

        self.start_date = date_time
        self.timestep_dates()
        self.load()

    def load_timestep_thread(self, date_times, data_queue):

        for date_time in date_times[1:]:
            self.load_timestep(date_time)

            for variable in self.VARIABLES:
                data_queue[variable].put(
                    [date_time, getattr(self, variable).iloc[0]])

        self._logger.debug('Finished loading data')

    def parse_data(self, metadata, data):

        # the data may be returned as type=object, convert to numeric
        # correct for the timezone
        for key in data.keys():
            data[key] = data[key].apply(pd.to_numeric)
            data[key] = data[key].tz_localize(tz=self.time_zone)

        self.metadata = metadata

        idx = data['air_temp'].index
        cols = data['air_temp'].columns

        self._logger.debug('Loading air_temp')
        self.air_temp = data['air_temp']

        # calculate vapor pressure
        self._logger.debug('Loading vapor_pressure')
        vp = rh2vp(
            data['air_temp'].values,
            data['relative_humidity'].values)
        self.vapor_pressure = pd.DataFrame(vp, index=idx, columns=cols)

        # calculate the wind speed and wind direction
        self._logger.debug('Loading wind_speed and wind_direction')
        min_speed = 0.47

        # calculate the wind speed
        s = np.sqrt(data['wind_u']**2 + data['wind_v']**2)
        s[s < min_speed] = min_speed

        # calculate the wind direction
        d = np.degrees(np.arctan2(data['wind_v'], data['wind_u']))
        ind = d < 0
        d[ind] = d[ind] + 360
        self.wind_speed = pd.DataFrame(s, index=idx, columns=cols)
        self.wind_direction = pd.DataFrame(d, index=idx, columns=cols)

        self._logger.debug('Loading precip')
        self.precip = pd.DataFrame(data['precip_int'], index=idx, columns=cols)

        self._logger.debug('Loading solar')
        solar = pd.DataFrame(data['short_wave'], index=idx, columns=cols)
        self._logger.debug('Calculating cloud factor')
        self.cloud_factor = get_hrrr_cloud(
            solar, self.metadata, self._logger,
            self.topo.basin_lat, self.topo.basin_long)
