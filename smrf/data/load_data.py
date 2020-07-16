import logging

import numpy as np
import utm

from smrf.data import InputCSV, InputGribHRRR, InputNetcdf, InputWRF


class InputData():
    """
    Class for loading and storing the data, either from
    - CSV file
    - HRRR grib files
    - WRF
    - Generic gridded NetCDF


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
        'precip': 'precipitation',
        'wind_speed': 'wind',
        'wind_direction': 'wind',
        'cloud_factor': 'cloud_factor',
        'thermal': 'thermal'
    }

    DATA_FUNCTIONS = {
        InputCSV.DATA_TYPE: InputCSV,
        InputWRF.DATA_TYPE: InputWRF,
        InputNetcdf.DATA_TYPE: InputNetcdf,
        InputGribHRRR.DATA_TYPE: InputGribHRRR
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

        if 'csv' in self.smrf_config:
            self.data_type = InputCSV.DATA_TYPE
            data_inputs = {
                'stations': self.smrf_config['csv']['stations'],
                'config': self.smrf_config['csv']
            }

        elif 'gridded' in self.smrf_config:
            self.data_type = self.smrf_config['gridded']['data_type']
            data_inputs = {
                'bbox': self.bbox,
                'config': self.smrf_config['gridded'],
                'topo': self.topo
            }

        # load the data
        self.load_class = self.DATA_FUNCTIONS[self.data_type](
            self.start_date,
            self.end_date,
            **data_inputs)
        self.load_class.load()

        self.set_variables()

        self.metadata_pixel_location()

        if self.data_type == InputCSV.DATA_TYPE:
            self.load_class.check_colocation()

    def set_variables(self):
        """Set the instance attributes for each variable
        """

        for variable in self.VARIABLES:
            d = getattr(self.load_class, variable, None)
            if variable == 'metadata':
                setattr(self, variable, d)
            elif d is not None:
                d = d.tz_convert(tz=self.time_zone)
                setattr(self, variable, d[self.start_date:self.end_date])

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
