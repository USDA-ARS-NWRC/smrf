import logging

import numpy as np
import utm

from smrf.data import mysql_data
from smrf.data import LoadCSV, LoadWRF, LoadNetcdf, LoadGribHRRR


class LoadData():
    """
    Class for loading and storing the data, either from
    - CSV file
    - MySQL database
    - Add other sources here

    Inputs to data() are:
    - dataConfig, either the [csv] or [mysql] section
    - start_date, datetime object
    - end_date, datetime object
    - dataType, either 'csv' or 'mysql'

    The data will be loaded into a Pandas dataframe

    """

    VARIABLES = [
        'air_temp',
        'vapor_pressure',
        'precip',
        'wind_speed',
        'wind_direction',
        'cloud_factor',
        'thermal',
        'metadata'
    ]

    # Data variables and which module they belong to
    MODULE_VARIABLES = {
        'air_temp': 'air_temp',
        'vapor_pressure': 'vapor_pressure',
        'precip': 'precip',
        'wind_speed': 'wind',
        'wind_direction': 'wind',
        'cloud_factor': 'cloud_factor',
        'thermal': 'thermal'
    }

    db_config_vars = ['user',
                      'password',
                      'host',
                      'database',
                      'port',
                      'metadata',
                      'data_table',
                      'station_table',
                      'stations',
                      'client']

    DATA_FUNCTIONS = {
        'csv': LoadCSV,
        'wrf': LoadWRF,
        'netcdf': LoadNetcdf,
        'hrrr_grib': LoadGribHRRR
    }

    # degree offset for a buffer around the model domain in degrees
    OFFSET = 0.1

    def __init__(self, smrf_config, start_date, end_date, topo):

        self.smrf_config = smrf_config
        self.start_date = start_date
        self.end_date = end_date
        self.time_zone = start_date.tzinfo
        self.topo = topo

        self._logger = logging.getLogger(__name__)

        # get the buffer gridded data domain extents in lat long
        self.model_domain_grid()

        data_inputs = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'time_zone': self.time_zone,
            'topo': self.topo,
            'bbox': self.bbox
        }

        if 'csv' in self.smrf_config:
            self.data_type = 'csv'
            data_inputs['stations'] = self.smrf_config['csv']['stations']
            data_inputs['config'] = self.smrf_config['csv']

        elif 'gridded' in self.smrf_config:
            self.data_type = self.smrf_config['gridded']['data_type']
            data_inputs['config'] = self.smrf_config['gridded']

        # load the data
        load_func = self.DATA_FUNCTIONS[self.data_type](**data_inputs)
        load_func.load()

        for variable in self.VARIABLES:
            d = getattr(load_func, variable, None)
            if variable == 'metadata':
                setattr(self, variable, d)
            elif d is not None:
                d = d.tz_convert(tz=self.time_zone)
                setattr(self, variable, d[self.start_date:self.end_date])

        self.metadata_pixel_location()

        if self.data_type == 'csv':
            load_func.check_colocation()

    def metadata_pixel_location(self):
        """Set the pixel location in the topo for each station
        """

        self.metadata['xi'] = self.metadata.apply(
            lambda row: self.find_pixel_location(
                row,
                self.topo.x,
                'utm_x'), axis=1)
        self.metadata['yi'] = self.metadata.apply(
            lambda row: self.find_pixel_location(
                row,
                self.topo.y,
                'utm_y'), axis=1)

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
        dlat[0] -= self.OFFSET
        dlat[1] += self.OFFSET
        dlon[0] -= self.OFFSET
        dlon[1] += self.OFFSET

        self.dlat = dlat
        self.dlon = dlon

        # This is placed long, lat on purpose as thats the HRRR class expects
        self.bbox = np.array([self.dlon[0], self.dlat[0],
                              self.dlon[1], self.dlat[1]])

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

    def find_pixel_location(self, row, vec, a):
        """
        Find the index of the stations X/Y location in the model domain

        Args:
            row (pandas.DataFrame): metadata rows
            vec (nparray): Array of X or Y locations in domain
            a (str): Column in DataFrame to pull data from (i.e. 'X')

        Returns:
            Pixel value in vec where row[a] is located
        """
        return np.argmin(np.abs(vec - row[a]))

    # def load_from_mysql(self):
    #     """
    #     Load the data from a mysql database
    #     """

    #     self._logger.info('Reading data from MySQL database')

    #     # open the database connection
    #     data = mysql_data.database(self.dataConfig['user'],
    #                                self.dataConfig['password'],
    #                                self.dataConfig['host'],
    #                                self.dataConfig['database'],
    #                                self.dataConfig['port'])

    #     # ---------------------------------------------------
    #     # determine if it's stations or client
    #     sta = self.stations

    #     c = None
    #     stable = None
    #     if 'client' in self.dataConfig.keys():
    #         c = self.dataConfig['client']
    #         stable = self.dataConfig['station_table']

    #     # Determine what table for the metadata
    #     mtable = self.dataConfig['metadata']

    #     # Raise an error if neither stations or client provided
    #     if (sta is None) & (c is None):
    #         raise Exception('Error in configuration file for [mysql],'
    #                         ' must specify either "stations" or "client"')

    #     self._logger.debug('Loading metadata from table %s' % mtable)

    #     # ---------------------------------------------------
    #     # load the metadata
    #     self.metadata = data.metadata(mtable, station_ids=sta,
    #                                   client=c, station_table=stable)

    #     self._logger.debug('%i stations loaded' % self.metadata.shape[0])

    #     # ---------------------------------------------------
    #     # get a list of the stations
    #     station_ids = self.metadata.index.tolist()

    #     # get the correct column names if specified, along with variable names
    #     db_var_names = [val for key, val in self.dataConfig.items()
    #                     if key not in self.db_config_vars]
    #     variables = [x for x in self.dataConfig.keys()
    #                  if x not in self.db_config_vars]

    #     # get the data
    #     # dp is a dictionary of dataframes
    #     dp = data.get_data(
    #         self.dataConfig['data_table'],
    #         station_ids,
    #         self.start_date,
    #         self.end_date, db_var_names,
    #         time_zone=self.time_zone
    #     )

    #     # go through and extract the data
    #     for v in variables:
    #         # MySQL Data is TZ aware. So convert just in case non utc
    #         # is passed.
    #         dfv = dp[self.dataConfig[v]]
    #         setattr(self, v, dfv)
