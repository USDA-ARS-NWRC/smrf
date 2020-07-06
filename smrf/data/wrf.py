import logging

import pandas as pd
import numpy as np
import netCDF4 as nc
import pytz
from smrf.utils.utils import apply_utm
from smrf.envphys.vapor_pressure import satvp


class LoadWRF():

    WRF_VARIABLES = [
        'GLW',
        'T2',
        'DWPT',
        'UGRD',
        'VGRD',
        'CLDFRA',
        'RAINNC'
    ]

    def __init__(self, *args, **kwargs):

        for keys in kwargs.keys():
            setattr(self, keys, kwargs[keys])

        self._logger = logging.getLogger(__name__)

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
        f = nc.Dataset(self.config['wrf_file'])

        # get the values that are in the modeling domain
        ind = (f.variables['XLAT'] >= self.bbox[1]) & \
            (f.variables['XLAT'] <= self.bbox[3]) & \
            (f.variables['XLONG'] >= self.bbox[0]) & \
            (f.variables['XLONG'] <= self.bbox[2])

        mlat = f.variables['XLAT'][:][ind]
        mlon = f.variables['XLONG'][:][ind]
        mhgt = f.variables['HGT'][:][ind]

        # GET THE METADATA
        # create some fake station names based on the index
        a = np.argwhere(ind)
        primary_id = ['grid_y%i_x%i' % (i[0], i[1]) for i in a]
        self._logger.debug('{} grid cells within model domain'.format(len(a)))

        # create a metadata dataframe to store all the grid info
        metadata = pd.DataFrame(index=primary_id,
                                columns=('utm_x', 'utm_y', 'latitude',
                                         'longitude', 'elevation'))

        metadata['latitude'] = mlat.flatten()
        metadata['longitude'] = mlon.flatten()
        metadata['elevation'] = mhgt.flatten()
        metadata = metadata.apply(apply_utm,
                                  args=(self.topo.zone_number,),
                                  axis=1)

        self.metadata = metadata

        # GET THE TIMES
        t = f.variables['Times']
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

        # subset the times to only those needed
        time_ind = (time >= self.start_date) & (time <= self.end_date)
        time = time[time_ind]

        # GET THE DATA, ONE AT A TIME
        self._logger.debug('Loading air_temp')
        self.air_temp = pd.DataFrame(index=time, columns=primary_id)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = f.variables['T2'][time_ind, i[0], i[1]] - 273.15
            self.air_temp[g] = v

        self._logger.debug('Loading dew_point and calculating vapor_pressure')
        self.dew_point = pd.DataFrame(index=time, columns=primary_id)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = f.variables['DWPT'][time_ind, i[0], i[1]]
            self.dew_point[g] = v

        self._logger.debug('Calculating vapor_pressure')
        vp = satvp(self.dew_point.values)
        self.vapor_pressure = pd.DataFrame(
            vp, index=time, columns=primary_id)

        self._logger.debug('Loading thermal')
        self.thermal = pd.DataFrame(index=time, columns=primary_id)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = f.variables['GLW'][time_ind, i[0], i[1]]
            self.thermal[g] = v

        self._logger.debug('Loading cloud_factor')
        self.cloud_factor = pd.DataFrame(index=time, columns=primary_id)
        cf = 1 - np.mean(f.variables['CLDFRA'][time_ind, :], axis=1)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            v = cf[:, i[0], i[1]]
            self.cloud_factor[g] = v

        self._logger.debug('Loading wind_speed and wind_direction')
        self.wind_speed = pd.DataFrame(index=time, columns=primary_id)
        self.wind_direction = pd.DataFrame(index=time, columns=primary_id)
        min_speed = 0.47

        u10 = f.variables['UGRD'][time_ind, :]
        v10 = f.variables['VGRD'][time_ind, :]

        # calculate the wind speed
        s = np.sqrt(u10**2 + v10**2)
        s[s < min_speed] = min_speed

        # calculate the wind direction
        d = np.degrees(np.arctan2(v10, u10))

        ind = d < 0
        d[ind] = d[ind] + 360

        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])

            self.wind_speed[g] = s[:, i[0], i[1]]
            self.wind_direction[g] = d[:, i[0], i[1]]

        self._logger.debug('Loading precip')
        self.precip = pd.DataFrame(index=time, columns=primary_id)
        precip = np.diff(f.variables['RAINNC'][time_ind, :], axis=0)
        for i in a:
            g = 'grid_y%i_x%i' % (i[0], i[1])
            self.precip[g] = np.concatenate(([0], precip[:, i[0], i[1]]))

        # # correct for the timezone and get only the desired dates
        # for v in self.variables:
        #     d = getattr(self, v)
        #     setattr(self, v, d.tz_convert(tz=self.time_zone))
