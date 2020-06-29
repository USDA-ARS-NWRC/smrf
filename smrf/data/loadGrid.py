import logging

import netCDF4 as nc
import numpy as np
import pandas as pd
import pytz
import utm
from weather_forecast_retrieval import hrrr

from smrf.envphys.solar.cloud import get_hrrr_cloud
from smrf.envphys.vapor_pressure import rh2vp, satvp


class grid():
    """
    Class for loading and storing the data, either from
    a gridded dataset in:
    - NetCDF format
    - other format

    Inputs to data() are:
    - dataConfig, from the [gridded] section
    - start_date, datetime object
    - end_date, datetime object

    """

    def __init__(self, dataConfig, topo, start_date, end_date,
                 time_zone='UTC', dataType='wrf',
                 forecast_flag=False, day_hour=0, n_forecast_hours=18):

        self.dataConfig = dataConfig
        self.dataType = dataType
        self.start_date = start_date
        self.end_date = end_date
        self.time_zone = time_zone
        self.forecast_flag = forecast_flag
        self.day_hour = day_hour
        self.n_forecast_hours = n_forecast_hours
        self.topo = topo

        # degree offset for a buffer around the model domain in degrees
        self.offset = 0.1

        # The data that will be output
        self.variables = ['air_temp', 'vapor_pressure', 'precip', 'wind_speed',
                          'wind_direction', 'cloud_factor', 'thermal']

        # get the buffer gridded data domain extents in lat long
        self.dlat, self.dlon = self.model_domain_grid()

        # This is placed long, lat on purpose as thats the HRRR class expects
        self.bbox = np.array([self.dlon[0], self.dlat[0],
                              self.dlon[1], self.dlat[1]])

        self._logger = logging.getLogger(__name__)

        # load the data
        if dataType == 'wrf':
            self.load_from_wrf()
        elif dataType == 'netcdf':
            self.load_from_netcdf()
        elif dataType == 'hrrr_grib':
            self.load_from_hrrr()
        else:
            raise Exception('Could not resolve dataType')

    def model_domain_grid(self):
        '''
        Retrieve the bounding box for the gridded data by adding a buffer to
        the extents of the topo domain.

        Returns:
            tuple: (dlat, dlon) Domain latitude and longitude extents
        '''
        dlat = np.zeros((2,))
        dlon = np.zeros_like(dlat)

        # Convert the UTM extents to lat long extents
        ur = self.get_latlon(np.max(self.topo.x), np.max(self.topo.y))
        ll = self.get_latlon(np.min(self.topo.x), np.min(self.topo.y))

        # Put into numpy arrays for convenience later
        dlat[0], dlon[0] = ll
        dlat[1], dlon[1] = ur

        # add a buffer
        dlat[0] -= self.offset
        dlat[1] += self.offset
        dlon[0] -= self.offset
        dlon[1] += self.offset

        return dlat, dlon

    def load_from_hrrr(self):
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
            self.dataConfig['hrrr_directory']
        ))

        # forecast hours for each run hour
        if not self.forecast_flag:
            fcast = [0]
        else:
            fcast = range(self.n_forecast_hours + 1)

        metadata, data = hrrr.HRRR(
            external_logger=self._logger
        ).get_saved_data(
            self.start_date,
            self.end_date,
            self.bbox,
            output_dir=self.dataConfig['hrrr_directory'],
            force_zone_number=self.topo.zone_number,
            forecast=fcast,
            forecast_flag=self.forecast_flag,
            day_hour=self.day_hour)

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

    def load_from_netcdf(self):
        """
        Load the data from a generic netcdf file

        Args:
            lat: latitude field in file, 1D array
            lon: longitude field in file, 1D array
            elev: elevation field in file, 2D array
            variable: variable name in file, 3D array
        """

        self._logger.info('Reading data coming from netcdf: {}'.format(
            self.dataConfig['netcdf_file'])
        )

        f = nc.Dataset(self.dataConfig['netcdf_file'], 'r')

        # GET THE LAT, LON, ELEV FROM THE FILE
        mlat = f.variables['lat'][:]
        mlon = f.variables['lon'][:]
        mhgt = f.variables['elev'][:]

        if mlat.ndim != 2 & mlon.ndim != 2:
            [mlon, mlat] = np.meshgrid(mlon, mlat)

        # get the values that are in the modeling domain
        ind = (mlat >= self.dlat[0]) & \
            (mlat <= self.dlat[1]) & \
            (mlon >= self.dlon[0]) & \
            (mlon <= self.dlon[1])

        mlat = mlat[ind]
        mlon = mlon[ind]
        mhgt = mhgt[ind]

        # GET THE METADATA
        # create some fake station names based on the index
        a = np.argwhere(ind)
        primary_id = ['grid_y%i_x%i' % (i[0], i[1]) for i in a]
        self._logger.debug('{} grid cells within model domain'.format(len(a)))

        # create a metadata dataframe to store all the grid info
        metadata = pd.DataFrame(index=primary_id,
                                columns=('X', 'Y', 'latitude',
                                         'longitude', 'elevation'))

        metadata['latitude'] = mlat.flatten()
        metadata['longitude'] = mlon.flatten()
        metadata['elevation'] = mhgt.flatten()
        metadata = metadata.apply(apply_utm,
                                  args=(self.topo.zone_number,),
                                  axis=1)

        self.metadata = metadata

        # GET THE TIMES
        t = f.variables['time']
        time = nc.num2date(t[:].astype(int), t.getncattr(
            'units'), t.getncattr('calendar'))
        # Drop milliseconds and prepare to use as pandas DataFrame index
        time = pd.DatetimeIndex(
            [str(tm.replace(microsecond=0)) for tm in time], tz=self.time_zone
        )

        # GET THE DATA, ONE AT A TIME
        for v in self.variables:

            if v in self.dataConfig:
                v_file = self.dataConfig[v]
                self._logger.debug('Loading {} from {}'.format(v, v_file))

                df = pd.DataFrame(index=time, columns=primary_id)
                for i in a:
                    g = 'grid_y%i_x%i' % (i[0], i[1])
                    df[g] = f.variables[v_file][:, i[0], i[1]]

                # deal with any fillValues
                try:
                    fv = f.variables[v_file].getncattr('_FillValue')
                    df.replace(fv, np.nan, inplace=True)
                except Exception:
                    pass

                # Set variable and subset by start and end time
                setattr(self, v, df[self.start_date:self.end_date])

    def load_from_wrf(self):
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

        self.wrf_variables = ['GLW', 'T2', 'DWPT', 'UGRD',
                              'VGRD', 'CLDFRA', 'RAINNC']

        self._logger.info('Reading data coming from WRF output: {}'.format(
            self.dataConfig['wrf_file']
        ))
        f = nc.Dataset(self.dataConfig['wrf_file'])

        # get the values that are in the modeling domain
        ind = (f.variables['XLAT'] >= self.dlat[0]) & \
            (f.variables['XLAT'] <= self.dlat[1]) & \
            (f.variables['XLONG'] >= self.dlon[0]) & \
            (f.variables['XLONG'] <= self.dlon[1])

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
                                columns=('X', 'Y', 'latitude',
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

        # correct for the timezone and get only the desired dates
        for v in self.variables:
            d = getattr(self, v)
            setattr(self, v, d.tz_convert(tz=self.time_zone))

    def get_latlon(self, utm_x, utm_y):
        '''
        Convert UTM coords to Latitude and longitude

        Args:
            utm_x: UTM easting in meters in the same zone/letter as the topo
            utm_y: UTM Northing in meters in the same zone/letter as the topo

        Returns:
            tuple: (lat,lon) latitude and longitude conversion from the UTM
                coordinates
        '''

        lat, lon = utm.to_latlon(utm_x, utm_y, self.topo.zone_number,
                                 northern=self.topo.northern_hemisphere)
        return lat, lon


def apply_utm(s, force_zone_number):
    """
    Calculate the utm from lat/lon for a series

    Args:
        s: pandas series with fields latitude and longitude
        force_zone_number: default None, zone number to force to

    Returns:
        s: pandas series with fields 'X' and 'Y' filled
    """
    p = utm.from_latlon(s.latitude, s.longitude,
                        force_zone_number=force_zone_number)
    s['X'] = p[0]
    s['Y'] = p[1]
    return s
