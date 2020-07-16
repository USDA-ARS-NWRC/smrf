
import numpy as np

from smrf.distribute import image_data
from smrf.envphys.core import envphys_c
from smrf.utils import utils


class vp(image_data.image_data):
    """
    The :mod:`~smrf.distribute.vapor_pressure.vp` class allows for variable
    specific distributions that go beyond the base class

    Vapor pressure is provided as an argument and is calculated from coincident
    air temperature and relative humidity measurements using utilities such as
    :mod:`smrf.envphys.vapor_pressure.rh2vp`. The vapor pressure is distributed
    instead of the relative humidity as it is an absolute measurement of the
    vapor within the atmosphere and will follow elevational trends (typically
    negative).  Were as relative humidity is a relative measurement which
    varies in complex ways over the topography.  From the distributed vapor
    pressure, the dew point is calculated for use by other distribution
    methods. The dew point temperature is further corrected to ensure that it
    does not exceed the distributed air temperature.

    Args:
        vpConfig: The [vapor_pressure] section of the configuration file

    Attributes:
        config: configuration from [vapor_pressure] section
        vapor_pressure: numpy matrix of the vapor pressure
        dew_point: numpy matrix of the dew point, calculated from
            vapor_pressure and corrected for dew_point greater than air_temp
        min: minimum value of vapor pressure is 10 Pa
        max: maximum value of vapor pressure is 7500 Pa
        stations: stations to be used in alphabetical order

    """

    variable = 'vapor_pressure'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
        'vapor_pressure': {
            'units': 'pascal',
            'standard_name': 'vapor_pressure',
            'long_name': 'Vapor pressure'
        },
        'dew_point': {
            'units': 'degree_Celcius',
            'standard_name': 'dew_point_temperature',
            'long_name': 'Dew point temperature'
        },
        'precip_temp': {
            'units': 'degree_Celcius',
            'standard_name': 'precip_temperature',
            'long_name': 'Precip temperature'
        }
    }

    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    BASE_THREAD_VARIABLES = frozenset([
        'vapor_pressure',
        'dew_point',
        'precip_temp'
    ])

    def __init__(self, vpConfig, precip_temp_method):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)

        # check and assign the configuration
        self.getConfig(vpConfig)

        # assign precip temp method
        self.precip_temp_method = precip_temp_method

        self._logger.debug('Created distribute.vapor_pressure')

    def initialize(self, topo, data, date_time=None):
        """
        Initialize the distribution, calls
        :mod:`smrf.distribute.image_data.image_data._initialize`. Preallocates
        the following class attributes to zeros:

        Args:
            topo: :mod:`smrf.data.loadTopo.Topo` instance contain topographic
                data and infomation
            data: data Pandas dataframe containing the station data,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.vapor_pressure')
        self.date_time = date_time
        self._initialize(topo, data.metadata)

        # get dem to pass to wet_bulb
        self.dem = topo.dem

    def distribute(self, data, ta):
        """
        Distribute air temperature given a Panda's dataframe for a single time
        step. Calls :mod:`smrf.distribute.image_data.image_data._distribute`.

        The following steps are performed when distributing vapor pressure:

        1. Distribute the point vapor pressure measurements
        2. Calculate dew point temperature using
            :mod:`smrf.envphys.core.envphys_c.cdewpt`
        3. Adjust dew point values to not exceed the air temperature

        Args:
            data: Pandas dataframe for a single time step from precip
            ta: air temperature numpy array that will be used for calculating
                dew point temperature

        """

        self._logger.debug('%s -- Distributing vapor_pressure' % data.name)

        # calculate the vapor pressure
        self._distribute(data)

        # set the limits
        self.vapor_pressure = utils.set_min_max(self.vapor_pressure,
                                                self.min,
                                                self.max)

        # calculate the dew point
        self._logger.debug('%s -- Calculating dew point' % data.name)

        # use the core_c to calculate the dew point
        dpt = np.zeros_like(self.vapor_pressure, dtype=np.float64)
        envphys_c.cdewpt(self.vapor_pressure,
                         dpt,
                         self.config['dew_point_tolerance'],
                         self.config['dew_point_nthreads'])

        # find where dpt > ta
        ind = dpt >= ta

        if (np.sum(ind) > 0):  # or np.sum(indm) > 0):
            dpt[ind] = ta[ind] - 0.2

        self.dew_point = dpt

        # calculate wet bulb temperature
        if self.precip_temp_method == 'wet_bulb':
            # initialize timestep wet_bulb
            wet_bulb = np.zeros_like(self.vapor_pressure, dtype=np.float64)
            # calculate wet_bulb
            envphys_c.cwbt(ta, dpt, self.dem,
                           wet_bulb, self.config['dew_point_tolerance'],
                           self.config['dew_point_nthreads'])
            # # store last time step of wet_bulb
            # self.wet_bulb_old = wet_bulb.copy()
            # store in precip temp for use in precip
            self.precip_temp = wet_bulb
        else:
            self.precip_temp = dpt

    def distribute_thread(self, smrf_queue, data_queue):
        """
        Distribute the data using threading. All data is provided and
        ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.vapor_pressure.vp.distribute` then puts the
        distributed data into the smrf_queue for:

        * :py:attr:`vapor_pressure`
        * :py:attr:`dew_point`

        Args:
            smrf_queue: smrf_queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """
        self._logger.info("Distributing {}".format(self.variable))

        for date_time in self.date_time:

            vp_data = data_queue['vapor_pressure'].get(date_time)
            ta = smrf_queue['air_temp'].get(date_time)

            self.distribute(vp_data, ta)

            smrf_queue[self.variable].put([date_time, self.vapor_pressure])
            smrf_queue['precip_temp'].put([date_time, self.precip_temp])
            smrf_queue['dew_point'].put([date_time, self.dew_point])
