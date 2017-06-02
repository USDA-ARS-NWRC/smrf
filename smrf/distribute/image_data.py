
# import pandas as pd
import numpy as np
from smrf.spatial import idw, dk, grid
import logging

__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2015-12-31"
__version__ = "0.2.2"


class image_data():
    """
    A base distribution method in SMRF that will ensure all variables are
    distributed in the same manner.  Other classes will be initialized
    using this base class.

    .. code-block:: Python

        class ta(smrf.distribute.image_data):
            '''
            This is the ta class extending the image_data base class
            '''

    Args:
        variable (str): Variable name for the class

    Returns:
        A :mod:`!smrf.distribute.image_data` class instance

    Attributes:
        variable: The name of the variable that this class will become
        [variable_name]: The :py:attr:`variable` will have the distributed data
        [other_attribute]: The distributed data can also be stored as another
            attribute specified in
            :mod:`~smrf.distribute.image_data._distribute`
        config: Parsed dictionary from the configuration file for the variable
        stations: The stations to be used for the variable, if set, in
            alphabetical order
        metadata: The metadata Pandas dataframe containing the station
            information from :mod:`smrf.data.loadData` or
            :mod:`smrf.data.loadGrid`
        idw: Inverse distance weighting instance from
            :mod:`smrf.spatial.idw.IDW`
        dk: Detrended kriging instance from :mod:`smrf.spatial.dk.dk.DK`
        grid: Gridded interpolation instance from :mod:`smrf.spatial.grid.GRID`

    """

    def __init__(self, variable):

        self.variable = variable
        setattr(self, variable, None)

        self.gridded = False

        self._base_logger = logging.getLogger(__name__)

    def getConfig(self, config):
        """
        Check the configuration that was set by the user for the variable
        that extended this class. Checks for standard distribution parameters
        that are common across all variables and assigns to the class instance.
        Sets the :py:attr:`config` and :py:attr:`stations` attributes.

        Args:
            config (dict): dict from the [variable]
                `section <configuration.html#variable-configuration>`_

        """

        # check for inverse distance weighting
        if 'distribution' in config:
            if config['distribution'] == 'idw':
                if 'detrend' not in config:
                    config['detrend'] = False

                if 'slope' in config:
                    if int(config['slope']) not in [-1, 0, 1]:
                        raise ValueError('''Slope value for detrending
                                            must be in [-1, 0, 1]''')
                    else:
                        config['slope'] = int(config['slope'])

                if 'power' in config:
                    if float(config['power']) < 0:
                        raise ValueError('IDW power must be greater than zero')
                    else:
                        config['power'] = float(config['power'])
                else:
                    config['power'] = 2

                if 'zeroValue' in config:
                    config['zeroValue'] = float(config['zeroValue'])
                else:
                    config['zeroValue'] = None

            # check of detrended kriging
            elif config['distribution'] == 'dk':
                if 'slope' in config:
                    if int(config['slope']) not in [-1, 0, 1]:
                        raise ValueError('''Slope value for detrending
                                            must be in [-1, 0, 1]''')
                    else:
                        config['slope'] = int(config['slope'])

                if 'nthreads' in config:
                    config['nthreads'] = int(config['nthreads'])
                else:
                    config['nthreads'] = 1

                if 'dk_nthreads' in config:
                    config['dk_nthreads'] = int(config['dk_nthreads'])
                else:
                    config['dk_nthreads'] = 1

                if 'regression_method' in config:
                    config['regression_method'] = \
                        int(config['regression_method'])
                else:
                    config['regression_method'] = 1

            # check of gridded interpolation
            elif config['distribution'] == 'grid':
                self.gridded = True
                if 'slope' in config:
                    if int(config['slope']) not in [-1, 0, 1]:
                        raise ValueError('''Slope value for detrending
                                            must be in [-1, 0, 1]''')
                    else:
                        config['slope'] = int(config['slope'])

                if 'detrend' not in config:
                    config['detrend'] = False

                if 'method' in config:
                    config['method'] = config['method'].lower()
                else:
                    config['method'] = 'linear'

                if 'mask' not in config:
                    config['mask'] = False

        self.getStations(config)
        self.config = config

    def getStations(self, config):
        """
        Determines the stations from the [variable] section of the
        configuration file.

        Args:
            config (dict): dict from the [variable]
            `section <configuration.html#variable-configuration>`_
        """

        # determine the stations that will be used, alphabetical order
        if 'stations' in config:
            stations = config['stations']
#             stations = map(str.strip, stations)
            stations.sort()
        else:
            stations = None

        self.stations = stations

    def _initialize(self, topo, metadata):
        """
        Initialize the distribution based on the parameters in
        :py:attr:`config`.

        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic
                data and infomation
            metadata: metadata Pandas dataframe containing the station metadata
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        Raises:
            Exception: If the distribution method could not be determined, must
                be idw, dk, or grid

        To do:
            - make a single call to the distribution initialization
            - each dist (idw, dk, grid) takes the same inputs and returns the
                same
        """

        # pull out the metadata subset
        if self.stations is not None:
            metadata = metadata.ix[self.stations]
        else:
            self.stations = metadata.index.values
        self.metadata = metadata

        mx = metadata.X.values
        my = metadata.Y.values
        mz = metadata.elevation.values

        if self.config['distribution'] == 'idw':
            # inverse distance weighting
            self.idw = idw.IDW(mx, my, topo.X, topo.Y, mz=mz,
                               GridZ=topo.dem, power=self.config['power'])

        elif self.config['distribution'] == 'dk':
            # detrended kriging
            self.dk = dk.DK(mx, my, mz, topo.X, topo.Y, topo.dem, self.config)

        elif self.config['distribution'] == 'grid':
            # linear interpolation between points
            self.grid = grid.GRID(self.config, mx, my, topo.X, topo.Y, mz=mz,
                                  GridZ=topo.dem, mask=topo.mask)

        else:
            raise Exception('''Could not determine the distribution
                                method for {}'''.format(self.variable))

    def distribute(self, data, other_attribute=None, zeros=None):
        """
        Distribute the data using the defined distribution method in
        :py:attr:`config`

        Args:
            data: Pandas dataframe for a single time step
            other_attribute (str): By defult, the distributed data matrix goes
                into self.variable but this specifies another attribute in self
            zeros: data values that should be treated as zeros (not used)

        Raises:
            Exception: If all input data is NaN
        """

        # get the data for the desired stations
        # this will also order it correctly how air_temp was initialized
        data = data[self.stations]

        if np.sum(data.isnull()) == data.shape[0]:
            raise Exception('''{}: All data values
                            are NaN'''.format(self.variable))

        if self.config['distribution'] == 'idw':
            if self.config['detrend']:
                v = self.idw.detrendedIDW(data.values,
                                          self.config['slope'],
                                          zeros=zeros)
            else:
                v = self.idw.calculateIDW(data.values)

        elif self.config['distribution'] == 'dk':
            v = self.dk.calculate(data.values)

        elif self.config['distribution'] == 'grid':
            if self.config['detrend']:
                v = self.grid.detrendedInterpolation(data.values,
                                                     self.config['slope'],
                                                     self.config['method'])
            else:
                v = self.grid.calculateInterpolation(data.values,
                                                     self.config['method'])

        if other_attribute is not None:
            setattr(self, other_attribute, v)
        else:
            setattr(self, self.variable, v)

    def post_processor(self, output_func):
        """
        Each distributed variable has the oppurtunity to do post processing on
        a sub variable. This is necessary in cases where the post proecessing
        might need to be done on a different timescale than that of the main
        loop.

        Should be redefined in the individual variable module.
        """
        pass
