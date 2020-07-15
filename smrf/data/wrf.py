import logging

import netCDF4 as nc
import numpy as np
import pandas as pd
import pytz

from smrf.data.netcdf import metadata_name_from_index
from smrf.envphys.vapor_pressure import satvp
from smrf.utils.utils import apply_utm


class InputWRF():

    DATA_TYPE = 'wrf'

    BASE_VARIABLES = {
        'air_temp': 'T2',
        'dew_point': 'DWPT',
        'precip': 'RAINNC'
    }

    WRF_VARIABLES = {
        'air_temp': 'T2',
        'dew_point': 'DWPT',
        'u10': 'UGRD',
        'v10': 'VGRD',
        'cloud_factor': 'CLDFRA',
        'precip': 'RAINNC'
    }

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

    def get_file_times(self):
        """Read the times from the WRF file and attempt to
        interpret the format.

        Raises:
            Exception: could not parse the times

        Returns:
            list: list of date times
        """

        t = self.file.variables['Times']
        t.set_auto_maskandscale(False)
        try:
            times = [('').join(v) for v in t]
        except TypeError:
            times = []
            for v in t:
                times.append(''.join([s.decode('utf-8') for s in v]))
        except Exception:
            raise Exception('Could not convert WRF times to readable format')

        times = [v.replace('_', ' ') for v in times]  # remove the underscore
        in_utc = str(self.time_zone).lower() == str(pytz.UTC).lower()
        time = pd.to_datetime(times, utc=in_utc)

        return time

    def get_metadata(self):

        # get the values that are in the modeling domain
        ind = (self.file.variables['XLAT'] >= self.bbox[1]) & \
            (self.file.variables['XLAT'] <= self.bbox[3]) & \
            (self.file.variables['XLONG'] >= self.bbox[0]) & \
            (self.file.variables['XLONG'] <= self.bbox[2])

        mlat = self.file.variables['XLAT'][:][ind]
        mlon = self.file.variables['XLONG'][:][ind]
        mhgt = self.file.variables['HGT'][:][ind]

        # GET THE METADATA
        # create some fake station names based on the index
        self.station_index = np.argwhere(ind)
        self.primary_id = [metadata_name_from_index(
            i) for i in self.station_index]
        self._logger.debug(
            '{} grid cells within model domain'.format(
                len(self.station_index)))

        # create a metadata dataframe to store all the grid info
        metadata = pd.DataFrame(index=self.primary_id,
                                columns=('utm_x', 'utm_y', 'latitude',
                                         'longitude', 'elevation'))

        metadata['latitude'] = mlat.flatten()
        metadata['longitude'] = mlon.flatten()
        metadata['elevation'] = mhgt.flatten()
        metadata = metadata.apply(apply_utm,
                                  args=(self.topo.zone_number,),
                                  axis=1)

        self.metadata = metadata

    def load(self):
        """
        Load the data from a netcdf file. This was setup to work with a WRF
        output file, i.e. wrf_out so it's going to look for the following
        variables:
        - Times
        - XLAT
        - XLONG
        - HGT
        - T2
        - DWPT
        - GLW
        - RAINNC
        - CLDFRA
        - UGRD
        - VGRD

        Each cell will be identified by grid_IX_IY

        """

        self._logger.info('Reading data coming from WRF output: {}'.format(
            self.config['wrf_file']
        ))
        self.file = nc.Dataset(self.config['wrf_file'])

        self.get_metadata()

        # GET THE TIMES
        time = self.get_file_times()
        time_ind = (time >= self.start_date) & (time <= self.end_date)
        time = time[time_ind]

        # GET THE DATA, ONE AT A TIME
        for variable, wrf_variable in self.BASE_VARIABLES.items():

            self._logger.debug(
                'Loading variable {} from WRF field {}'.format(
                    variable, wrf_variable))

            df = pd.DataFrame(index=time, columns=self.primary_id)
            for i in self.station_index:
                g = metadata_name_from_index(i)
                df[g] = self.file.variables[wrf_variable][time_ind, i[0], i[1]]

            # Set variable and subset by start and end time
            setattr(self, variable, df)

        # post process the loaded data
        self.air_temp = self.air_temp - 273.15

        self._logger.debug('Calculating vapor_pressure')
        vp = satvp(self.dew_point.values)
        self.vapor_pressure = pd.DataFrame(
            vp, index=time, columns=self.primary_id)

        self._logger.debug('Loading cloud_factor')
        self.cloud_factor = pd.DataFrame(index=time, columns=self.primary_id)
        cf = 1 - np.mean(self.file.variables['CLDFRA'][time_ind, :], axis=1)
        for i in self.station_index:
            g = metadata_name_from_index(i)
            v = cf[:, i[0], i[1]]
            self.cloud_factor[g] = v

        self._logger.debug('Loading wind_speed and wind_direction')
        self.wind_speed = pd.DataFrame(index=time, columns=self.primary_id)
        self.wind_direction = pd.DataFrame(index=time, columns=self.primary_id)

        u10 = self.file.variables['UGRD'][time_ind, :]
        v10 = self.file.variables['VGRD'][time_ind, :]

        # calculate the wind speed
        s = np.sqrt(u10**2 + v10**2)

        # calculate the wind direction
        d = np.degrees(np.arctan2(v10, u10))
        ind = d < 0
        d[ind] = d[ind] + 360

        for i in self.station_index:
            g = metadata_name_from_index(i)
            self.wind_speed[g] = s[:, i[0], i[1]]
            self.wind_direction[g] = d[:, i[0], i[1]]

        self._logger.debug('Loading precip')
        self.precip = self.precip.diff(axis=0)
        self.precip.iloc[0, :] = 0
