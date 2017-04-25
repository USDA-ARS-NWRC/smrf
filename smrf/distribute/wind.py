__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-04"
__version__ = "0.1.1"



import numpy as np
import logging, os
from smrf.distribute import image_data
from smrf.utils import utils
import netCDF4 as nc
# import matplotlib.pyplot as plt

class wind(image_data.image_data):
    """

    The :mod:`~smrf.distribute.wind.wind` class allows for variable specific distributions that
    go beyond the base class.

    Estimating wind speed and direction is complex terrain can be difficult due to the interaction
    of the local topography with the wind. The methods described here follow the work developed by
    Winstral and Marks (2002) and Winstral et al. (2009) :cite:`Winstral&Marks:2002` :cite:`Winstral&al:2009`
    which parameterizes the terrain based on the upwind direction. The underlying method calulates
    the maximum upwind slope (maxus) within a search distance to determine if a cell is sheltered or exposed.
    See :mod:`smrf.utils.wind.model` for a more in depth description. A maxus file (library) is used
    to load the upwind direction and maxus values over the dem. The following steps are performed when
    estimating the wind speed:

    1. Adjust measured wind speeds at the stations and determine the wind direction componenets
    2. Distribute the flat wind speed
    3. Distribute the wind direction components
    4. Simulate the wind speeds based on the distribute flat wind, wind direction, and maxus values

    After the maxus is calculated for multiple wind directions over the entire DEM, the
    measured wind speed and direction can be distirbuted. The first step is to adjust the measured
    wind speeds to estimate the wind speed if the site were on a flat surface. The adjustment uses
    the maxus value at the station location and an enhancement factor for the site based on the sheltering
    of that site to wind. A special consideration is performed when the station is on a peak, as artificially
    high wind speeds can be calcualted.  Therefore, if the station is on a peak, the minimum maxus value
    is choosen for all wind directions. The wind direction is also broken up into the u,v componenets.

    Next the flat wind speed, u wind direction component, and v wind direction compoenent are distributed
    using the underlying distribution methods. With the distributed flat wind speed and wind direction,
    the simulated wind speeds can be estimated. The distributed wind direction is binned into the upwind
    directions in the maxus library. This determines which maxus value to use for each pixel in the DEM.
    Each cell's maxus value is further enhanced for vegetation, with larger, more dense vegetation increasing
    the maxus value (more sheltering) and bare ground not enhancing the maxus value (exposed). With the
    adjusted maxus values, wind speed is estimated using the relationships in Winstral and Marks (2002) and
    Winstral et al. (2009) :cite:`Winstral&Marks:2002` :cite:`Winstral&al:2009` based on the distributed
    flat wind speed and each cell's maxus value.

    When gridded data is provided, the methods outlined above are not performed due to the unknown
    complexity of parameterizing the gridded dataset for using the maxus methods. Therefore, the
    wind speed and direction are distributed using the underlying distribution methods.

    Args:
        windConfig: The [wind] section of the configuration file

    Attributes:
        config: configuration from [vapor_pressure] section
        wind_speed: numpy matrix of the wind speed
        wind_direction: numpy matrix of the wind direction
        veg_type: numpy array for the veg type, from :py:attr:`smrf.data.loadTopo.topo.veg_type`
        _maxus_file: the location of the maxus NetCDF file
        maxus: the loaded library values from :py:attr:`_maxus_file`
        maxus_direction: the directions associated with the :py:attr:`maxus` values
        min: minimum value of wind is 0.447
        max: maximum value of wind is 35
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class :mod:`!smrf.distribute.wind.wind`
            that specifies the ``units`` and ``long_name`` for creating the NetCDF output file.
        variable: 'wind'

    """

    variable = 'wind'
    min = 0.447
    max = 35

    # these are variables that can be output
    output_variables = {'flatwind':{
                                  'units': 'm/s',
                                  'long_name': 'flatwind_wind_speed'
                                  },
                        'wind_speed':{
                                  'units': 'm/s',
                                  'long_name': 'wind_speed'
                                  },
                        'wind_direction':{
                                  'units': 'degrees',
                                  'long_name': 'wind_direction'
                                  }
                        }
    # these are variables that are operate at the end only and do not need to be written during main distribute loop
    post_process_variables = {}

    def __init__(self, windConfig, tempDir=None):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        self.getConfig(windConfig)

        if (tempDir is None) | (tempDir == 'WORKDIR'):
            tempDir = os.environ['WORKDIR']
        self.tempDir = tempDir

        if windConfig['distribution'] == 'grid':
            self.gridded = True

        else:
            # open the maxus netCDF
            self._maxus_file = nc.Dataset(self.config['maxus_netcdf'], 'r')
            self.maxus = self._maxus_file.variables['maxus'][:]
            self.maxus_direction = self._maxus_file.variables['direction'][:]
            self._maxus_file.close()
            self._logger.debug('Read data from %s' % self.config['maxus_netcdf'])

            # check maxus defaults
            if 'station_default' not in self.config:
                self.config['station_default'] = 11.4
            if 'veg_default' not in self.config:
                self.config['veg_default'] = 11.4

            # get the veg values
            matching = [s for s in self.config.keys() if "veg_" in s]
            v = {}
            for m in matching:
                if m != 'veg_default':
                    ms = m.split('_')
                    v[ms[1]] = float(self.config[m])
            self.config['veg'] = v

            # peak value
            if 'peak' in self.config:
                self.config['peak'] = self.config['peak'].split(',')
            else:
                self.config['peak'] = None

        self._logger.debug('Created distribute.wind')



#     def __del__(self):
#         self._maxus_file.close()
#         self._logger.debug('Closed %s' % self._maxus_file)



    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls :mod:`smrf.distribute.image_data.image_data._initialize`.
        Checks for the enhancement factors for the stations and vegetation.

        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic data
                and infomation
            metadata: metadata Pandas dataframe containing the station metadata,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.wind')

        self._initialize(topo, metadata)

        if not self.gridded:
            self.veg_type = topo.veg_type

            # get the enhancements for the stations
            if 'enhancement' not in self.metadata.columns:
                self.metadata['enhancement'] = float(self.config['station_default'])

                for m in self.metadata.index:
                    if m.lower() in self.config:
                        self.metadata.loc[m, 'enhancement'] = float(self.config[m.lower()])




    def distribute(self, data_speed, data_direction):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        Follows the following steps for station measurements:

        1. Adjust measured wind speeds at the stations and determine the wind direction componenets
        2. Distribute the flat wind speed
        3. Distribute the wind direction components
        4. Simulate the wind speeds based on the distribute flat wind, wind direction, and maxus values

        Gridded interpolation distributes the given wind speed and direction.

        Args:
            data_speed: Pandas dataframe for single time step from wind_speed
            data_direction: Pandas dataframe for single time step from wind_direction

        """

        self._logger.debug('%s Distributing wind_direction and wind_speed' % data_speed.name)

        data_speed = data_speed[self.stations]
        data_direction = data_direction[self.stations]

        if self.gridded:
            self._distribute(data_speed, other_attribute='wind_speed')

            # wind direction components at the station
            self.u_direction = np.sin(data_direction * np.pi/180)    # u
            self.v_direction = np.cos(data_direction * np.pi/180)    # v

            # distribute u_direction and v_direction
            self._distribute(self.u_direction, other_attribute='u_direction_distributed')
            self._distribute(self.v_direction, other_attribute='v_direction_distributed')

            # combine u and v to azimuth
            az = np.arctan2(self.u_direction_distributed, self.v_direction_distributed)*180/np.pi
            az[az < 0] = az[az < 0] + 360
            self.wind_direction = az

            self.wind_speed = utils.set_min_max(self.wind_speed, self.min, self.max)

        else:
            # calculate the maxus at each site
            self.stationMaxus(data_speed, data_direction)

            # distribute the flatwind
            self._distribute(self.flatwind, other_attribute='flatwind_distributed')

            # distribute u_direction and v_direction
            self._distribute(self.u_direction, other_attribute='u_direction_distributed')
            self._distribute(self.v_direction, other_attribute='v_direction_distributed')

            # Calculate simulated wind speed at each cell from flatwind
            self.simulateWind(data_speed)


    def distribute_thread(self, queue, data_speed, data_direction):
        """
        Distribute the data using threading and queue. All data is provided and ``distribute_thread``
        will go through each time step and call :mod:`smrf.distribute.wind.wind.distribute` then
        puts the distributed data into the queue for :py:attr:`wind_speed`.

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time

        """

        for t in data_speed.index:

            self.distribute(data_speed.ix[t], data_direction.ix[t])

            queue['wind_speed'].put( [t, self.wind_speed] )

    def simulateWind(self, data_speed):
        """
        Calculate the simulated wind speed at each cell from flatwind and the distributed directions.
        Each cell's maxus value is pulled from the maxus library based on the distributed wind
        direction. The cell's maxus is further adjusted based on the vegetation type and the
        factors provided in the [wind] section of the configuration file.

        Args:
            data_speed: Pandas dataframe for a single time step of wind speed to make the pixel
                locations same as the measured values
        """

        # combine u and v to azimuth
        az = np.arctan2(self.u_direction_distributed, self.v_direction_distributed)*180/np.pi
        az[az < 0] = az[az < 0] + 360


        dir_round_cell = np.ceil((az - self.nstep/2) / self.nstep) * self.nstep
        dir_round_cell[dir_round_cell < 0] = dir_round_cell[dir_round_cell < 0] + 360
        dir_round_cell[dir_round_cell == -0] = 0
        dir_round_cell[dir_round_cell == 360] = 0

        cellmaxus = np.zeros(dir_round_cell.shape)
        cellwind = np.zeros(dir_round_cell.shape)

        dir_unique = np.unique(dir_round_cell)
        for d in dir_unique:
            # find all values for matching direction
            ind = dir_round_cell == d
            i = np.argwhere(self.maxus_direction == d)[0][0]
            cellmaxus[ind] = self.maxus[i][ind]

        # correct for veg
        for i,v in enumerate(self.config['veg']):
            cellmaxus[self.veg_type == int(v)] += self.config['veg'][v]

        # correct unreasonable values
        cellmaxus[cellmaxus > 32] = 32
        cellmaxus[cellmaxus < -32] = -32

        # determine wind
        factor = float(self.config['reduction_factor'])
        ind = cellmaxus < -30.10
        cellwind[ind] = factor * self.flatwind_distributed[ind] * 4.211

        ind = (cellmaxus > -30.10) & (cellmaxus < -21.3)
        c = np.abs(cellmaxus[ind])
        cellwind[ind] = factor * self.flatwind_distributed[ind] * (1.756507 - 0.1678945 * c + 0.01927844 * np.power(c,2) - 0.0003651592 * np.power(c, 3))

        ind = (cellmaxus > -21.3) & (cellmaxus < 0)
        c = np.abs(cellmaxus[ind])
        cellwind[ind] = factor * self.flatwind_distributed[ind] * (1.0 + 0.1031717 * c - 0.008003561 * np.power(c,2) + 0.0003996581 * np.power(c,3))

        ind = cellmaxus > 30.10
        cellwind[ind] = self.flatwind_distributed[ind] / 4.211

        ind = (cellmaxus < 30.10) & (cellmaxus > 21.3)
        c = cellmaxus[ind]
        cellwind[ind] = self.flatwind_distributed[ind] / (1.756507 - 0.1678945 * c + 0.01927844 * np.power(c,2) - 0.0003651592 * np.power(c,3))

        ind = (cellmaxus < 21.3) & (cellmaxus >= 0)
        c = cellmaxus[ind]
        cellwind[ind] = self.flatwind_distributed[ind] / (1.0 + 0.1031717 * c - 0.008003561 * np.power(c,2) + 0.0003996581 * np.power(c,3))


        # Convert from 3m to 5m wind speed
        cellwind *= 1.07985;

        # preseve the measured values
        cellwind[self.metadata.xi, self.metadata.xi] = data_speed

        # check for NaN
        nans, x = utils.nan_helper(cellwind)

        if np.sum(nans) > 0:
            cellwind[nans] = np.interp(x(nans), x(~nans), cellwind[~nans])

        self.wind_speed = utils.set_min_max(cellwind, self.min, self.max)
        self.wind_direction = az



    def stationMaxus(self, data_speed, data_direction):
        """
        Determine the maxus value at the station given the wind direction.
        Can specify the enhancemet for each station or use the default, along
        with whether or not the station is on a peak which will ensure that
        the station cannot be sheltered. The station enhancement and peak stations
        are specified in the [wind] section of the configuration file. Calculates the
        following for each station:

        * :py:attr:`flatwind`
        * :py:attr:`u_direction`
        * :py:attr:`v_direction`

        Args:
            data_speed: wind_speed data frame for single time step
            data_direction: wind_direction data frame for single time step

        """

        #------------------------------------------------------------------------------
        # Get data and site maxus value
        flatwind = data_speed.copy()

        # number of bins that the maxus library was calculated for
        self.nbins = len(self.maxus_direction)
        self.nstep = 360/self.nbins

        for m in self.metadata.index:

            # pixel locations
            xi = self.metadata.loc[m, 'xi']
            yi = self.metadata.loc[m, 'yi']
            e = self.metadata.loc[m,'enhancement']

            # maxus value at the station
            if not np.isnan(data_direction[m]):

                if m in self.config['peak']:
                    val_maxus = np.min(self.maxus[:, yi, xi] + e)

                else:
                    idx = int(np.ceil((data_direction[m] - self.nstep/2) / self.nstep) * self.nstep)
                    if idx == 360:
                        idx = 0 # special case when 360=0
                    ind = self.maxus_direction == idx

                    val_maxus = self.maxus[ind, yi, xi] + e


                # correct unreasonable values
                if val_maxus > 35: val_maxus = 35
                if val_maxus < -35: val_maxus = -35

                ma = np.abs(val_maxus)

                # Lapse all measurements to flat terrain (i.e. maxus = 0)
                if (ma > 21.3 and ma < 30.0):
                    expVal = 1.756507 - 0.1678945 * ma + 0.01927844 * np.power(ma,2) - 0.0003651592 * np.power(ma,3)
                elif (ma >= 30.0):
                    expVal = 4.21
                else:
                    expVal = 1.0 + 0.1031717 * (ma) - 0.008003561 * np.power(ma,2) + 0.0003996581 * np.power(ma,3)

                if val_maxus > 0:
                    flatwind.loc[m] = data_speed[m] * expVal
                else:
                    flatwind.loc[m] = data_speed[m] / expVal
            else:
                flatwind.loc[m] = np.NaN


        self.flatwind = flatwind

        # wind direction components at the station
        self.u_direction = np.sin(data_direction * np.pi/180)    # u
        self.v_direction = np.cos(data_direction * np.pi/180)    # v



# def cellMaxus(cellmaxus, flatwind, factor):
#     """
#     Apply the equations for the cell maxus
#     """
#
#     if cellmaxus < -30.10:
#         cellwind = factor * flatwind * 4.211
#     elif (cellmaxus > -30.10) & (cellmaxus < -21.3):
#         cellwind = factor * flatwind * (1.756507 - 0.1678945 * np.abs(cellmaxus) + 0.01927844 * np.power(np.abs(cellmaxus),2) - 0.0003651592 * np.power(np.abs(cellmaxus), 3))
#     elif (cellmaxus > -21.3) & (cellmaxus < 0):
#         cellwind = factor * flatwind * (1.0 + 0.1031717 * np.abs(cellmaxus) - 0.008003561 * np.power(np.abs(cellmaxus),2) + 0.0003996581 * np.power(np.abs(cellmaxus),3))
#     elif cellmaxus > 30.10:
#         cellwind = flatwind / 4.211
#     elif (cellmaxus < 30.10) & (cellmaxus > 21.3):
#         cellwind = flatwind / (1.756507 - 0.1678945 * (cellmaxus) + 0.01927844 * np.power(cellmaxus,2) - 0.0003651592 * np.power(cellmaxus,3))
#     elif (cellmaxus < 21.3) & (cellmaxus >= 0):
#         cellwind = flatwind / (1.0 + (0.1031717 * cellmaxus) - (0.008003561 * np.power(cellmaxus,2)) + (0.0003996581 * np.power(cellmaxus,3)))
#
#     return cellwind
