
import glob
import logging
import os

import netCDF4 as nc
import numpy as np
import pandas as pd
import pytz

from smrf.distribute import image_data
from smrf.utils import utils
from smrf.distribute.wind.winstral import WinstralWindModel


class Wind(image_data.image_data):
    """

    The :mod:`~smrf.distribute.wind.wind` class allows for variable specific
    distributions that go beyond the base class.

    Estimating wind speed and direction is complex terrain can be difficult due
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

    When gridded data is provided, the methods outlined above are not performed
    due to the unknown complexity of parameterizing the gridded dataset for
    using the maxus methods. Therefore, the wind speed and direction are
    distributed using the underlying distribution methods.

    Args:
        self.config: The [wind] section of the configuration file

    Attributes:
        config: configuration from [vapor_pressure] section
        wind_speed: numpy matrix of the wind speed
        wind_direction: numpy matrix of the wind direction
        veg_type: numpy array for the veg type, from
            :py:attr:`smrf.data.loadTopo.topo.veg_type`
        _maxus_file: the location of the maxus NetCDF file
        maxus: the loaded library values from :py:attr:`_maxus_file`
        maxus_direction: the directions associated with the :py:attr:`maxus`
            values
        min: minimum value of wind is 0.447
        max: maximum value of wind is 35
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class
            :mod:`!smrf.distribute.wind.wind` that specifies the ``units`` and
            ``long_name`` for creating the NetCDF output file.
        variable: 'wind'

    """

    variable = 'wind'

    # these are variables that can be output
    output_variables = {
        'flatwind': {
            'units': 'm/s',
            'standard_name': 'flatwind_wind_speed',
            'long_name': 'Simulated wind on a flat surface'
        },
        'wind_speed': {
            'units': 'm/s',
            'standard_name': 'wind_speed',
            'long_name': 'Wind speed'
        },
        'wind_direction': {
            'units': 'degrees',
            'standard_name': 'wind_direction',
            'long_name': 'Wind direction'
        }
    }
    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    def __init__(self, config):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        self.smrf_config = config
        self.getConfig(config['wind'])

        distribute_drifts = False
        if self.smrf_config["precip"]["precip_rescaling_model"] == "winstral":
            distribute_drifts = True

        if self.config['distribution'] == 'grid':
            self.gridded = True
            self.distribute_drifts = False

            # wind ninja parameters
            self.wind_ninja_dir = self.config['wind_ninja_dir']
            self.wind_ninja_dxy = self.config['wind_ninja_dxdy']
            self.wind_ninja_pref = self.config['wind_ninja_pref']
            if self.config['wind_ninja_tz'] is not None:
                self.wind_ninja_tz = pytz.timezone(
                    self.config['wind_ninja_tz'].title())

            self.start_date = pd.to_datetime(
                self.smrf_config['time']['start_date'])
            self.grid_data = self.smrf_config['gridded']['data_type']

        else:
            self.wind_model = WinstralWindModel(
                self.smrf_config, distribute_drifts)

        self._logger.debug('Created distribute.wind')

    def initialize(self, topo, data):
        """
        Initialize the distribution, calls
        :mod:`smrf.distribute.image_data.image_data._initialize`. Checks for
        the enhancement factors for the stations and vegetation.

        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic
                data and infomation
            data: data Pandas dataframe containing the station data,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.wind')

        if not self.gridded or self.config['wind_ninja_dir'] is not None:
            self.wind_model.initialize(topo, data)

        else:
            self._initialize(topo, data.metadata)
            self.wind_model = self
            self.wind_model.flatwind = None
            self.wind_model.cellmaxus = None
            self.wind_model.dir_round_cell = None

    def distribute(self, data_speed, data_direction, t):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        Follows the following steps for station measurements:

        1. Adjust measured wind speeds at the stations and determine the wind
            direction componenets
        2. Distribute the flat wind speed
        3. Distribute the wind direction components
        4. Simulate the wind speeds based on the distribute flat wind, wind
            direction, and maxus values

        Gridded interpolation distributes the given wind speed and direction.

        Args:
            data_speed: Pandas dataframe for single time step from wind_speed
            data_direction: Pandas dataframe for single time step from
                wind_direction
            t: time stamp

        """

        self._logger.debug('{} Distributing wind_direction and wind_speed'
                           .format(data_speed.name))

        data_speed = data_speed[self.wind_model.stations]
        data_direction = data_direction[self.wind_model.stations]

        if self.gridded and self.wind_ninja_dir is None:

            self._distribute(data_speed, other_attribute='wind_speed')

            # wind direction components at the station
            self.u_direction = np.sin(data_direction * np.pi/180)    # u
            self.v_direction = np.cos(data_direction * np.pi/180)    # v

            # distribute u_direction and v_direction
            self._distribute(self.u_direction,
                             other_attribute='u_direction_distributed')
            self._distribute(self.v_direction,
                             other_attribute='v_direction_distributed')

            # combine u and v to azimuth
            az = np.arctan2(self.u_direction_distributed,
                            self.v_direction_distributed)*180/np.pi
            az[az < 0] = az[az < 0] + 360
            self.wind_direction = az

        else:
            self.wind_model.distribute(data_speed, data_direction)

        for v in self.output_variables.keys():
            setattr(self, v, getattr(self.wind_model, v))

        # set min and max
        self.wind_speed = utils.set_min_max(self.wind_speed,
                                            self.min,
                                            self.max)

    def distribute_thread(self, queue, data_speed, data_direction):
        """
        Distribute the data using threading and queue. All data is provided and
        ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.wind.wind.distribute` then puts the distributed
        data into the queue for :py:attr:`wind_speed`.

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """
        self._logger.info("Distributing {}".format(self.variable))

        for t in data_speed.index:

            self.distribute(data_speed.loc[t], data_direction.loc[t], t)

            queue['wind_speed'].put([t, self.wind_model.wind_speed])
            queue['wind_direction'].put([t, self.wind_model.wind_direction])
            queue['flatwind'].put([t, self.wind_model.flatwind])
            queue['cellmaxus'].put([t, self.wind_model.cellmaxus])
            queue['dir_round_cell'].put([t, self.wind_model.dir_round_cell])

    def convert_wind_ninja(self, t):
        """
        Convert the WindNinja ascii grids back to the SMRF grids and into the
        SMRF data streamself.

        Args:
            t:              datetime of timestep

        Returns:
            ws: wind speed numpy array
            wd: wind direction numpy array

        """
        # fmt_wn = '%Y-%m-%d_%H%M'
        fmt_wn = '%m-%d-%Y_%H%M'
        fmt_d = '%Y%m%d'

        # get the ascii files that need converted
        # file example tuol_09-20-2018_1900_200m_vel.prj
        # find timestamp of WindNinja file
        t_file = t.astimezone(self.wind_ninja_tz)

        fp_vel = os.path.join(self.wind_ninja_dir,
                              'data{}'.format(t.strftime(fmt_d)),
                              'wind_ninja_data',
                              '{}_{}_{:d}m_vel.asc'.format(self.wind_ninja_pref,
                                                           t_file.strftime(
                                                               fmt_wn),
                                                           self.wind_ninja_dxy))

        # make sure files exist
        if not os.path.isfile(fp_vel):
            raise ValueError(
                '{} in windninja convert module does not exist!'.format(fp_vel))

        data_vel = np.loadtxt(fp_vel, skiprows=6)
        data_vel_int = data_vel.flatten()

        # interpolate to the SMRF grid from the WindNinja grid
        g_vel = utils.grid_interpolate(data_vel_int, self.vtx,
                                       self.wts, self.X.shape)

        # flip because it comes out upsidedown
        g_vel = np.flipud(g_vel)
        # log law scale
        g_vel = g_vel * self.ln_wind_scale

        # Don't get angle if not distributing drifts
        if self.distribute_drifts:
            fp_ang = os.path.join(self.wind_ninja_dir,
                                  'data{}'.format(t.strftime(fmt_d)),
                                  'wind_ninja_data',
                                  '{}_{}_{:d}m_ang.asc'.format(self.wind_ninja_pref,
                                                               t_file.strftime(
                                                                   fmt_wn),
                                                               self.wind_ninja_dxy))

            if not os.path.isfile(fp_ang):
                raise ValueError(
                    '{} in windninja convert module does not exist!'.format(fp_ang))

            data_ang = np.loadtxt(fp_ang, skiprows=6)
            data_ang_int = data_ang.flatten()

            g_ang = utils.grid_interpolate(data_ang_int, self.vtx,
                                           self.wts, self.X.shape)

            g_ang = np.flipud(g_ang)

        else:
            g_ang = None

        return g_vel, g_ang
