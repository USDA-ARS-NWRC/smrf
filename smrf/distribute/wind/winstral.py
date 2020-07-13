import logging

import netCDF4 as nc
import numpy as np
import pandas as pd

from smrf.distribute import image_data
from smrf.utils import utils


class WinstralWindModel(image_data.image_data):
    """Estimating wind speed and direction is complex terrain can be difficult due
    to the interaction of the local topography with the wind. The methods
    described here follow the work developed by Winstral and Marks (2002) and
    Winstral et al. (2009) :cite:`Winstral&Marks:2002` :cite:`Winstral&al:2009`
    which parameterizes the terrain based on the upwind direction. The
    underlying method calulates the maximum upwind slope (maxus) within a
    search distance to determine if a cell is sheltered or exposed. See
    :mod:`smrf.utils.wind.model` for a more in depth description. A maxus file
    (library) is used to load the upwind direction and maxus values over the
    dem. The following steps are performed when estimating the wind speed:

    1. Adjust measured wind speeds at the stations and determine the wind
       direction componenets
    2. Distribute the flat wind speed
    3. Distribute the wind direction components
    4. Simulate the wind speeds based on the distribute flat wind, wind
       direction, and maxus values

    After the maxus is calculated for multiple wind directions over the entire
    DEM, the measured wind speed and direction can be distirbuted. The first
    step is to adjust the measured wind speeds to estimate the wind speed if
    the site were on a flat surface. The adjustment uses the maxus value at the
    station location and an enhancement factor for the site based on the
    sheltering of that site to wind. A special consideration is performed when
    the station is on a peak, as artificially high wind speeds can be
    calcualted.  Therefore, if the station is on a peak, the minimum maxus
    value is choosen for all wind directions. The wind direction is also broken
    up into the u,v componenets.

    Next the flat wind speed, u wind direction component, and v wind direction
    compoenent are distributed using the underlying distribution methods. With
    the distributed flat wind speed and wind direction, the simulated wind
    speeds can be estimated. The distributed wind direction is binned into the
    upwind directions in the maxus library. This determines which maxus value
    to use for each pixel in the DEM. Each cell's maxus value is further
    enhanced for vegetation, with larger, more dense vegetation increasing the
    maxus value (more sheltering) and bare ground not enhancing the maxus value
    (exposed). With the adjusted maxus values, wind speed is estimated using
    the relationships in Winstral and Marks (2002) and Winstral et al. (2009)
    :cite:`Winstral&Marks:2002` :cite:`Winstral&al:2009` based on the
    distributed flat wind speed and each cell's maxus value.
    """

    VARIABLE = 'wind'

    BASE_THREAD_VARIABLES = frozenset([
        'flatwind',
        'cellmaxus',
        'dir_round_cell'
    ])

    def __init__(self, smrf_config):
        """Initialize the WinstralWindModel

        Arguments:
            smrf_config {UserConfig} -- entire smrf config
            distribute_drifts {bool} -- distribute drifts if true

        Raises:
            IOError: if maxus file does not match topo size
        """

        image_data.image_data.__init__(self, self.VARIABLE)

        self._logger = logging.getLogger(__name__)

        self.smrf_config = smrf_config
        self.getConfig(smrf_config['wind'])
        # self.distribute_drifts = distribute_drifts

        self._logger.debug('Creating the WinstralWindModel')

        # open the maxus netCDF
        self._maxus_file = nc.Dataset(self.config['maxus_netcdf'], 'r')
        self.maxus = self._maxus_file.variables['maxus'][:]
        self.maxus_direction = self._maxus_file.variables['direction'][:]
        self._maxus_file.close()

        # Maxus must be the the same size as the topo.
        topo_nc = nc.Dataset(self.smrf_config['topo']['filename'], 'r')
        t_shape = topo_nc.variables['dem'].shape
        topo_nc.close()

        if t_shape != self.maxus[0].shape:
            raise IOError("\nMaxus file must be generated using the topo to"
                          " be valid. Maxus netcdf shape = {} and topo"
                          " netcdf shape = {}".format(t_shape,
                                                      self.maxus.shape))

        self._logger.debug('Read data from {}'
                           .format(self.config['maxus_netcdf']))

        # get the veg values
        matching = [s for s in self.config.keys() if "veg_" in s]
        v = {}
        for m in matching:
            ms = m.split('_')
            if type(self.config[m]) == list:
                v[ms[1]] = float(self.config[m][0])
            else:
                v[ms[1]] = float(self.config[m])

        self.veg = v

    def initialize(self, topo, data):
        """Initialize the model with data

        Arguments:
            topo {topo class} -- Topo class
            data {data object} -- SMRF data object
        """

        self._logger.debug('Initializing the WinstralWindModel')

        self._initialize(topo, data.metadata)

        self.veg_type = topo.veg_type

        # meshgrid points
        self.X = topo.X
        self.Y = topo.Y

        # get the enhancements for the stations
        if 'enhancement' not in self.metadata.columns:
            self.metadata['enhancement'] = \
                float(self.config['station_default'])

            for m in self.metadata.index:
                sta_e = m.lower()
                if sta_e in self.config:
                    if type(self.config[sta_e]) == list:
                        enhancement = self.config[sta_e][0]
                    else:
                        enhancement = self.config[sta_e]

                    self.metadata.loc[m, 'enhancement'] = \
                        float(enhancement)

        # if not self.distribute_drifts:
        # we have to pass these to precip, so make them none
        # if we won't use them, or they will be overwritten later
        # self.dir_round_cell = None
        # self.cellmaxus = None

    def distribute(self, data_speed, data_direction):
        """Distribute the wind for the model

        Follows the following steps for station measurements:

        1. Adjust measured wind speeds at the stations and determine the wind
            direction componenets
        2. Distribute the flat wind speed
        3. Distribute the wind direction components
        4. Simulate the wind speeds based on the distribute flat wind, wind
            direction, and maxus values

        Arguments:
            data_speed {DataFrame} -- wind speed data frame
            data_direction {DataFrame} -- wind direction data frame
        """

        # calculate the maxus at each site
        self.stationMaxus(data_speed, data_direction)

        # distribute the flatwind
        self._distribute(self.flatwind_point,
                         other_attribute='flatwind')

        # distribute u_direction and v_direction
        self._distribute(self.u_direction,
                         other_attribute='u_direction_distributed')
        self._distribute(self.v_direction,
                         other_attribute='v_direction_distributed')

        # Calculate simulated wind speed at each cell from flatwind
        self.simulateWind(data_speed)

    def simulateWind(self, data_speed):
        """
        Calculate the simulated wind speed at each cell from flatwind and the
        distributed directions. Each cell's maxus value is pulled from the
        maxus library based on the distributed wind direction. The cell's maxus
        is further adjusted based on the vegetation type and the factors
        provided in the [wind] section of the configuration file.

        Args:
            data_speed: Pandas dataframe for a single time step of wind speed
                to make the pixel locations same as the measured values
        """

        # combine u and v to azimuth
        az = np.arctan2(self.u_direction_distributed,
                        self.v_direction_distributed)*180/np.pi
        az[az < 0] = az[az < 0] + 360

        dir_round_cell = np.ceil((az - self.nstep/2) / self.nstep) * self.nstep
        dir_round_cell[dir_round_cell <
                       0] = dir_round_cell[dir_round_cell < 0] + 360
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
        dynamic_mask = np.ones(cellmaxus.shape)
        for k, v in self.veg.items():
            # Adjust veg types that were specified by the user
            if k != 'default':
                ind = self.veg_type == int(k)
                dynamic_mask[ind] = 0
                cellmaxus[ind] += v

        # Apply the veg default to those that weren't messed with
        if self.veg['default'] != 0:
            cellmaxus[dynamic_mask == 1] += self.veg['default']

        # correct unreasonable values
        cellmaxus[cellmaxus > 32] = 32
        cellmaxus[cellmaxus < -32] = -32

        # determine wind
        factor = float(self.config['reduction_factor'])
        ind = cellmaxus < -30.10
        cellwind[ind] = factor * self.flatwind[ind] * 4.211

        ind = (cellmaxus > -30.10) & (cellmaxus < -21.3)
        c = np.abs(cellmaxus[ind])
        cellwind[ind] = factor * self.flatwind[ind] * \
            (1.756507 - 0.1678945 * c + 0.01927844 * np.power(c, 2) -
             0.0003651592 * np.power(c, 3))

        ind = (cellmaxus > -21.3) & (cellmaxus < 0)
        c = np.abs(cellmaxus[ind])
        cellwind[ind] = factor * self.flatwind[ind] * \
            (1.0 + 0.1031717 * c - 0.008003561 * np.power(c, 2) +
             0.0003996581 * np.power(c, 3))

        ind = cellmaxus > 30.10
        cellwind[ind] = self.flatwind[ind] / 4.211

        ind = (cellmaxus < 30.10) & (cellmaxus > 21.3)
        c = cellmaxus[ind]
        cellwind[ind] = self.flatwind[ind] / \
            (1.756507 - 0.1678945 * c + 0.01927844 * np.power(c, 2) -
             0.0003651592 * np.power(c, 3))

        ind = (cellmaxus < 21.3) & (cellmaxus >= 0)
        c = cellmaxus[ind]
        cellwind[ind] = self.flatwind[ind] / \
            (1.0 + 0.1031717 * c - 0.008003561 * np.power(c, 2) +
             0.0003996581 * np.power(c, 3))

        # Convert from 3m to 5m wind speed
        cellwind *= 1.07985

        # preseve the measured values
        cellwind[self.metadata.yi, self.metadata.xi] = data_speed

        # check for NaN
        nans, x = utils.nan_helper(cellwind)

        if np.sum(nans) > 0:
            cellwind[nans] = np.interp(x(nans), x(~nans), cellwind[~nans])

        self.wind_speed = utils.set_min_max(cellwind, self.min, self.max)
        self.wind_direction = az
        self.cellmaxus = cellmaxus
        self.dir_round_cell = dir_round_cell

    def stationMaxus(self, data_speed, data_direction):
        """
        Determine the maxus value at the station given the wind direction.
        Can specify the enhancemet for each station or use the default, along
        with whether or not the station is on a peak which will ensure that
        the station cannot be sheltered. The station enhancement and peak
        stations are specified in the [wind] section of the configuration
        file. Calculates the following for each station:

        * :py:attr:`flatwind`
        * :py:attr:`u_direction`
        * :py:attr:`v_direction`

        Args:
            data_speed: wind_speed data frame for single time step
            data_direction: wind_direction data frame for single time step

        """

        # ----------------------------------------
        # Get data and site maxus value
        flatwind = data_speed.copy()

        # number of bins that the maxus library was calculated for
        self.nbins = len(self.maxus_direction)
        self.nstep = 360/self.nbins

        for m in self.metadata.index:
            # pixel locations
            xi = self.metadata.loc[m, 'xi']
            yi = self.metadata.loc[m, 'yi']
            e = self.metadata.loc[m, 'enhancement']

            # maxus value at the station
            if not pd.isnull(data_direction[m]):
                if self.config['station_peak'] is not None:
                    if m.upper() in self.config['station_peak']:
                        val_maxus = np.min(self.maxus[:, yi, xi] + e)

                else:
                    idx = int(np.ceil((data_direction[m] - self.nstep/2) /
                                      self.nstep) * self.nstep)
                    if idx == 360:
                        idx = 0  # special case when 360=0
                    ind = self.maxus_direction == idx

                    val_maxus = self.maxus[ind, yi, xi] + e

                # correct unreasonable values
                if val_maxus > 35:
                    val_maxus = 35
                if val_maxus < -35:
                    val_maxus = -35

                ma = np.abs(val_maxus)

                # Lapse all measurements to flat terrain (i.e. maxus = 0)
                if (ma > 21.3 and ma < 30.0):
                    expVal = 1.756507 - 0.1678945 * ma + \
                        0.01927844 * np.power(ma, 2) - \
                        0.0003651592 * np.power(ma, 3)
                elif (ma >= 30.0):
                    expVal = 4.21
                else:
                    expVal = 1.0 + 0.1031717 * (ma) - \
                        0.008003561 * np.power(ma, 2) + \
                        0.0003996581 * np.power(ma, 3)

                if val_maxus > 0:
                    flatwind.loc[m] = data_speed[m] * expVal
                else:
                    flatwind.loc[m] = data_speed[m] / expVal
            else:
                flatwind.loc[m] = np.NaN

        self.flatwind_point = flatwind

        # wind direction components at the station
        self.u_direction = np.sin(data_direction * np.pi/180)    # u
        self.v_direction = np.cos(data_direction * np.pi/180)    # v
