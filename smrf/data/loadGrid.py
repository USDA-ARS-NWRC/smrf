import numpy as np
import netCDF4 as nc
import pandas as pd
import logging
import os
import utm
import pytz
from smrf.envphys import phys
from smrf.envphys.radiation import get_hrrr_cloud

try:
    from weather_forecast_retrieval import hrrr
except:
    pass



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
                 time_zone='UTC', dataType='wrf', tempDir=None,
                 forecast_flag=False, day_hour=0, n_forecast_hours=18):

        if (tempDir is None) | (tempDir == 'WORKDIR'):
            tempDir = os.environ['WORKDIR']

        self.tempDir = tempDir
        self.dataConfig = dataConfig
        self.dataType = dataType
        self.start_date = start_date
        self.end_date = end_date
        self.time_zone = time_zone
        self.forecast_flag = forecast_flag
        self.day_hour = day_hour
        self.n_forecast_hours = n_forecast_hours

        # degree offset for a buffer around the model domain
        self.offset = 0.1

        self.force_zone_number = None
        if 'zone_number' in dataConfig:
            self.force_zone_number = dataConfig['zone_number']

        # The data that will be output
        self.variables = ['air_temp', 'vapor_pressure', 'precip', 'wind_speed',
                          'wind_direction', 'cloud_factor', 'thermal']

        # get the bounds of the model so that only the values inside
        # the model domain are used
        self.x = topo.x
        self.y = topo.y
        self.lat = topo.topoConfig['basin_lat']
        self.lon = topo.topoConfig['basin_lon']

        # get the zone number and the bounding box
        u = utm.from_latlon(topo.topoConfig['basin_lat'],
                            topo.topoConfig['basin_lon'],
                            self.force_zone_number)
        self.zone_number = u[2]
        self.zone_letter = u[3]

        ur = np.array(utm.to_latlon(np.max(self.x), np.max(self.y), self.zone_number, self.zone_letter))
        ll = np.array(utm.to_latlon(np.min(self.x), np.min(self.y), self.zone_number, self.zone_letter))

        buff = 0.1 # buffer of bounding box in degrees
        ur += buff
        ll -= buff
        self.bbox = np.append(np.flipud(ll), np.flipud(ur))


        self._logger = logging.getLogger(__name__)

        # load the data
        if dataType == 'wrf':
            self.load_from_wrf()
        elif dataType == 'netcdf':
            self.load_from_netcdf()
        elif dataType == 'hrrr':
            self.load_from_hrrr()
        else:
            raise Exception('Could not resolve dataType')

#         # correct for the timezone
#         for v in self.variables:
#             d = getattr(self, v)
#             setattr(self, v, d.tz_localize(tz=self.time_zone))

    def model_domain_grid(self):

        dlat = np.zeros((2,))
        dlon = np.zeros_like(dlat)
        dlat[0], dlon[0] = utm.to_latlon(np.min(self.x), np.min(self.y),
                                         int(self.dataConfig['zone_number']),
                                         self.dataConfig['zone_letter'])
        dlat[1], dlon[1] = utm.to_latlon(np.max(self.x), np.max(self.y),
                                         int(self.dataConfig['zone_number']),
                                         self.dataConfig['zone_letter'])
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
            self.dataConfig['directory']
            ))

        # forecast hours for each run hour
        if not self.forecast_flag:
            fcast = [0]
        else:
            fcast = range(self.n_forecast_hours + 1)

        metadata, data = hrrr.HRRR(external_logger=self._logger).get_saved_data(
            self.start_date,
            self.end_date,
            self.bbox,
            output_dir=self.dataConfig['directory'],
            force_zone_number=self.force_zone_number,
            forecast=fcast,
            forecast_flag=self.forecast_flag,
            day_hour=self.day_hour)

        # the data may be returned as type=object, convert to numeric
        # correct for the timezone
        for key in data.keys():
            df = data[key].apply(pd.to_numeric)
            df = df.tz_localize(tz=self.time_zone)
            df = df[self.start_date:self.end_date]
            data[key] = df

        self.metadata = metadata

        idx = data['air_temp'].index
        cols = data['air_temp'].columns

        self._logger.debug('Loading air_temp')
        self.air_temp = data['air_temp']

        # calculate vapor pressure
        self._logger.debug('Loading vapor_pressure')
        vp = phys.rh2vp(data['air_temp'].values, data['relative_humidity'].values)
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
        # solar_beam = pd.DataFrame(data['solar_beam'], index=idx, columns=cols)
        # solar_diffuse = pd.DataFrame(data['solar_diffuse'], index=idx, columns=cols)
        # solar = solar_beam + solar_diffuse
        solar = pd.DataFrame(data['short_wave'], index=idx, columns=cols)
        self._logger.debug('Calculating cloud factor')
        self.cloud_factor = get_hrrr_cloud(solar, self.metadata, self._logger,
                                           self.lat, self.lon)

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
                            self.dataConfig['file'])
                          )

        f = nc.Dataset(self.dataConfig['file'], 'r')

        # GET THE LAT, LON, ELEV FROM THE FILE
        mlat = f.variables['lat'][:]
        mlon = f.variables['lon'][:]
        mhgt = f.variables['elev'][:]

        if mlat.ndim != 2 & mlon.ndim !=2:
            [mlon, mlat] = np.meshgrid(mlon, mlat)

        # get that grid cells in the model domain
        dlat, dlon = self.model_domain_grid()

        # get the values that are in the modeling domain
        ind = (mlat >= dlat[0]) & \
            (mlat <= dlat[1]) & \
            (mlon >= dlon[0]) & \
            (mlon <= dlon[1])

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
                                  args=(self.force_zone_number,),
                                  axis=1)

        self.metadata = metadata

        # GET THE TIMES
        t = f.variables['time']
        time = nc.num2date(t[:].astype(int), t.getncattr('units'), t.getncattr('calendar'))
        time = [tm.replace(microsecond=0) for tm in time] # drop the milliseconds

        # subset the times to only those needed
#         tzinfo = pytz.timezone(self.time_zone)
#         time = []
#         for t in tt:
#             time.append(t.replace(tzinfo=tzinfo))
#         time = np.array(time)

#         time_ind = (time >= pd.to_datetime(self.start_date)) & \
#                    (time <= pd.to_datetime(self.end_date))
#         time = time[time_ind]

#         time_idx = np.where(time_ind)[0]

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
                except:
                    pass
                df = df[self.start_date:self.end_date]
                setattr(self, v, df.tz_localize(tz=self.time_zone))

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
#         self.variables = ['thermal','air_temp','dew_point','wind_speed',
#                             'wind_direction','cloud_factor','precip']



        self._logger.info('Reading data coming from WRF output: {}'.format(
            self.dataConfig['file']
            ))
        f = nc.Dataset(self.dataConfig['file'])

        # DETERMINE THE MODEL DOMAIN AREA IN THE GRID
        dlat, dlon = self.model_domain_grid()

        # get the values that are in the modeling domain
        ind = (f.variables['XLAT'] >= dlat[0]) & \
            (f.variables['XLAT'] <= dlat[1]) & \
            (f.variables['XLONG'] >= dlon[0]) & \
            (f.variables['XLONG'] <= dlon[1])

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
                                  args=(self.force_zone_number,),
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
        time = pd.to_datetime(times)

        # subset the times to only those needed
        time_ind = (time >= pd.to_datetime(self.start_date)) & \
                   (time <= pd.to_datetime(self.end_date))
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
        satvp = phys.satvp(self.dew_point.values)
        self.vapor_pressure = pd.DataFrame(satvp, index=time, columns=primary_id)

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
            setattr(self, v, d.tz_localize(tz=self.time_zone))


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
