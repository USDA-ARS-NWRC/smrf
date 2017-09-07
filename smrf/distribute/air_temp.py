
# import numpy as np
import logging
from smrf.distribute import image_data

__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2015-12-30"
__version = "0.2.5"


class ta(image_data.image_data):
    """
    The :mod:`~smrf.distribute.air_temp.ta` class allows for variable specific
    distributions that go beyond the base class.

    Air temperature is a relatively simple variable to distribute as it does
    not rely on any other variables, but has many variables that depend on it.
    Air temperature typically has a negative trend with elevation and performs
    best when detrended. However, even with a negative trend, it is possible to
    have instances where the trend does not apply, for example a temperature
    inversion or cold air pooling.  These types of conditions will have
    unintended concequences on variables that use the distributed air
    temperature.

    Args:
        taConfig: The [air_temp] section of the configuration file

    Attributes:
        config: configuration from [air_temp] section
        air_temp: numpy array of the air temperature
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class
            :mod:`!smrf.distribute.air_temp.ta` that specifies the ``units``
            and ``long_name`` for creating the NetCDF output file.
        variable: 'air_temp'

    """

    variable = 'air_temp'

    # these are variables that can be output
    output_variables = {'air_temp': {
                                     'units': 'degree_Celsius',
                                     'standard_name': 'air_temperature',
                                     'long_name': 'Air temperature'
                                     }
                        }

    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    def __init__(self, taConfig):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        self.getConfig(taConfig)

        self._logger.debug('Created distribute.air_temp')

    def initialize(self, topo, data):
        """
        Initialize the distribution, soley calls
        :mod:`smrf.distribute.image_data.image_data._initialize`.

        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic
                data and infomation
            metadata: metadata Pandas dataframe containing the station metadata
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.air_temp')
        self._initialize(topo, data.metadata)

    def distribute(self, data):
        """
        Distribute air temperature given a Panda's dataframe for a single time
        step. Calls :mod:`smrf.distribute.image_data.image_data._distribute`.

        Args:
            data: Pandas dataframe for a single time step from air_temp

        """

        self._logger.debug('{} -- Distributing air_temp'.format(data.name))

        self._distribute(data)

    def distribute_thread(self, queue, data):
        """
        Distribute the data using threading and queue. All data is provided
        and ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.air_temp.ta.distribute` then puts the distributed
        data into ``queue['air_temp']``.

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time

        """

        for t in data.index:

            self.distribute(data.ix[t])

            queue[self.variable].put([t, self.air_temp])
