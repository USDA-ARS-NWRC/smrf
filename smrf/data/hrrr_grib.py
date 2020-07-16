import logging

import numpy as np
import pandas as pd
from weather_forecast_retrieval.hrrr import HRRR

from smrf.envphys.solar.cloud import get_hrrr_cloud
from smrf.envphys.vapor_pressure import rh2vp


class InputGribHRRR():

    DATA_TYPE = 'hrrr_grib'

    VARIABLES = [
        'air_temp',
        'vapor_pressure',
        'precip',
        'wind_speed',
        'wind_direction',
        'cloud_factor'
    ]

    def __init__(self, start_date, end_date, bbox=None,
                 topo=None, config=None):

        self.start_date = start_date
        self.end_date = end_date
        self.topo = topo
        self.bbox = bbox
        self.config = config
        self.time_zone = start_date.tzinfo

        if topo is None:
            raise Exception('Must supply topo to InputWRF')

        if bbox is None:
            raise Exception('Must supply bbox to InputWRF')

        self._logger = logging.getLogger(__name__)

        if self.config['hrrr_load_method'] == 'timestep':
            self._timedelta_steps = pd.to_timedelta(20, 'minutes')
            self.timestep_dates()
            self.cf_memory = None

        self.hrrr = HRRR(external_logger=self._logger)

    def timestep_dates(self):
        self.end_date = self.start_date + self._timedelta_steps

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
        self.check_cloud_factor()

    def load_timestep_thread(self, date_times, data_queue):
        """Load HRRR within a thread and add the data to the data
        queue.

        Args:
            date_times (list): list of the simulation date_times
            data_queue (dict): dict of the data queues
        """

        for date_time in date_times[1:]:
            self.load_timestep(date_time)

            for variable in self.VARIABLES:
                data_queue[variable].put(
                    [date_time, getattr(self, variable).iloc[0]])

        self._logger.debug('Finished loading data')

    def parse_data(self, metadata, data):
        """Parse the data from HRRR into dataframes for SMRF

        Args:
            metadata (DataFrame): metadata DataFrame
            data (dict): dictionary of DataFrames from HRRR
        """

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
        self._logger.debug('Calculating vapor_pressure')
        vp = rh2vp(
            data['air_temp'].values,
            data['relative_humidity'].values)
        self.vapor_pressure = pd.DataFrame(vp, index=idx, columns=cols)

        # calculate the wind speed and wind direction
        self._logger.debug('Loading wind_speed and wind_direction')

        s = np.sqrt(data['wind_u']**2 + data['wind_v']**2)

        d = np.degrees(np.arctan2(data['wind_v'], data['wind_u']))
        ind = d < 0
        d[ind] = d[ind] + 360
        self.wind_speed = pd.DataFrame(s, index=idx, columns=cols)
        self.wind_direction = pd.DataFrame(d, index=idx, columns=cols)

        # precip
        self._logger.debug('Loading precip')
        self.precip = pd.DataFrame(data['precip_int'], index=idx, columns=cols)

        # cloud factor
        self._logger.debug('Loading solar')
        solar = pd.DataFrame(data['short_wave'], index=idx, columns=cols)
        self._logger.debug('Calculating cloud factor')
        self.cloud_factor = get_hrrr_cloud(
            solar, self.metadata,
            self.topo.basin_lat, self.topo.basin_long)

    def check_cloud_factor(self):
        """Check the cloud factor when in the timestep mode.
        This will fill NaN values as they happen by linearly
        interpolating from the last hour (i.e. copy it). This
        is similar to how `get_hrrr_cloud` with the difference
        being that it won't interpolate over the entire night.
        """

        if self.cf_memory is None:
            self.cf_memory = self.cloud_factor

            # if initial cloud factor is at night, default to clear sky
            if self.cf_memory.isnull().values.any():
                self.cf_memory[:] = 1

        else:
            self.cf_memory = pd.concat(
                [self.cf_memory.tail(1), self.cloud_factor])

        self.cf_memory = self.cf_memory.interpolate(method='linear').ffill()

        if self.cf_memory.isnull().values.any():
            self._logger.error('There are NaN values in the cloud factor')

        self.cloud_factor = self.cf_memory.tail(1)
