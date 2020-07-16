
import logging

import numpy as np

from smrf.distribute import image_data
from smrf.distribute.wind.wind_ninja import WindNinjaModel
from smrf.distribute.wind.winstral import WinstralWindModel
from smrf.utils import utils


class Wind(image_data.image_data):
    """
    The :mod:`~smrf.distribute.wind.wind` class allows for variable specific
    distributions that go beyond the base class.

    Three distribution methods are available for the Wind class:

    1. Winstral and Marks 2002 method for maximum upwind slope (maxus)
    2. Import WindNinja simulations
    3. Standard interpolation

    Args:
        self.config: The full SMRF configuration file

    Attributes:
        config: configuration from [wind] section
        wind_speed: numpy matrix of the wind speed
        wind_direction: numpy matrix of the wind direction
        veg_type: numpy array for the veg type, from
            :py:attr:`smrf.data.loadTopo.Topo.veg_type`
        _maxus_file: the location of the maxus NetCDF file
        maxus: the loaded library values from :py:attr:`_maxus_file`
        maxus_direction: the directions associated with the :py:attr:`maxus`
            values
        min: minimum value of wind is 0.447
        max: maximum value of wind is 35
        stations: stations to be used in alphabetical order

    """

    VARIABLE = 'wind'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
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

    BASE_THREAD_VARIABLES = frozenset([
        'wind_speed',
        'wind_direction'
    ])

    def __init__(self, config):

        # extend the base class
        image_data.image_data.__init__(self, self.VARIABLE)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        self.smrf_config = config
        self.getConfig(config['wind'])

        if self.check_wind_model_type('interp'):
            # Straight interpolation of the wind
            self.wind_model = self
            self.wind_model.flatwind = None
            self.wind_model.cellmaxus = None
            self.wind_model.dir_round_cell = None

        elif self.check_wind_model_type('wind_ninja'):
            self.wind_model = WindNinjaModel(self.smrf_config)

        elif self.check_wind_model_type('winstral'):
            self.wind_model = WinstralWindModel(self.smrf_config)

        self._logger.debug('Created distribute.wind')

    def check_wind_model_type(self, wind_model):
        """Check if the wind model is of a given type

        Args:
            wind_model (str): name of the wind model

        Returns:
            bool: True/False if the wind_model matches the config
        """

        return self.config['wind_model'] == wind_model

    def initialize(self, topo, data, date_time=None):
        """
        Initialize the distribution, calls
        :mod:`smrf.distribute.image_data.image_data._initialize`. Checks for
        the enhancement factors for the stations and vegetation.

        Args:
            topo: :mod:`smrf.data.loadTopo.Topo` instance contain topographic
                data and infomation
            data: data Pandas dataframe containing the station data,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.wind')
        self.date_time = date_time
        self.wind_model._initialize(topo, data.metadata)

        if self.check_wind_model_type('winstral'):
            self.add_thread_variables(self.wind_model.thread_variables)

        if not self.check_wind_model_type('interp'):
            self.wind_model.initialize(topo, data)

    def distribute(self, data_speed, data_direction, t):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute` for
        the `wind_model` chosen.

        Args:
            data_speed: Pandas dataframe for single time step from wind_speed
            data_direction: Pandas dataframe for single time step from
                wind_direction
            t: time stamp

        """

        self._logger.debug('{} Distributing wind_direction and wind_speed'
                           .format(data_speed.name))

        if self.check_wind_model_type('interp'):

            self._distribute(data_speed, other_attribute='wind_speed')

            # wind direction components at the station
            self.u_direction = np.sin(data_direction * np.pi/180)
            self.v_direction = np.cos(data_direction * np.pi/180)

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
                                            self.wind_model.min,
                                            self.wind_model.max)

    def distribute_thread(self, smrf_queue, data_queue):
        """
        Distribute the data using threading. All data is provided and
        ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.wind.wind.distribute` then puts the distributed
        data into the smrf_queue for :py:attr:`wind_speed`.

        Args:
            smrf_queue: smrf_queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """
        self._logger.info("Distributing {}".format(self.variable))

        for date_time in self.date_time:

            ws_data = data_queue['wind_speed'].get(date_time)
            wd_data = data_queue['wind_direction'].get(date_time)

            self.distribute(ws_data, wd_data, date_time)

            smrf_queue['wind_speed'].put(
                [date_time, self.wind_model.wind_speed])
            smrf_queue['wind_direction'].put(
                [date_time, self.wind_model.wind_direction])

            if self.check_wind_model_type('winstral'):
                smrf_queue['flatwind'].put(
                    [date_time, self.wind_model.flatwind])
                smrf_queue['cellmaxus'].put(
                    [date_time, self.wind_model.cellmaxus])
                smrf_queue['dir_round_cell'].put(
                    [date_time, self.wind_model.dir_round_cell])
