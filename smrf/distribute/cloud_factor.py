from smrf.distribute import image_data
from smrf.utils import utils


class cf(image_data.image_data):
    """
    The :mod:`~smrf.distribute.cloud_factor.cf` class allows for variable
    specific distributions that go beyond the base class. Cloud factor is
    a relatively simple variable to distribute as it does not rely on any
    other variables.

    Cloud factor is calculated as the ratio between measured incoming
    solar radiation and modeled clear sky radiation. A value of 0 means
    no incoming solar radiation (or very cloudy) and a value of 1 means
    sunny.

    Args:
        config: The [cloud_factor] section of the configuration file

    Attributes:
        config: configuration from [cloud_factor] section
        cloud_factor: numpy array of the cloud factor
        stations: stations to be used in alphabetical order

    """

    variable = 'cloud_factor'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
        'cloud_factor': {
            'units': 'None',
            'standard_name': 'cloud_factor',
            'long_name': 'cloud factor'
        }
    }

    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    BASE_THREAD_VARIABLES = frozenset([
        'cloud_factor'
    ])

    def __init__(self, config):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)

        # check and assign the configuration
        self.getConfig(config)
        self._logger.debug('Created distribute.cloud_factor')

    def initialize(self, topo, data, date_time=None):
        """
        Initialize the distribution, solely calls
        :mod:`smrf.distribute.image_data.image_data._initialize`.

        Args:
            topo: :mod:`smrf.data.loadTopo.Topo` instance contain topographic
                data and infomation
            metadata: metadata Pandas dataframe containing the station metadata
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.cloud_factor')
        self.date_time = date_time
        self._initialize(topo, data.metadata)

    def distribute(self, data):
        """
        Distribute cloud factor given a Panda's dataframe for a single time
        step. Calls :mod:`smrf.distribute.image_data.image_data._distribute`.

        Args:
            data: Pandas dataframe for a single time step from cloud_factor

        """

        self._logger.debug('{} Distributing cloud_factor'.format(data.name))

        self._distribute(data)
        self.cloud_factor = utils.set_min_max(self.cloud_factor, self.min,
                                              self.max)

    def distribute_thread(self, smrf_queue, data_queue):
        """
        Distribute the data using threading and queue. All data is provided
        and ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.cloud_factor.cf.distribute` then puts the
        distributed data into ``queue['cloud_factor']``.

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time

        """
        self._logger.info("Distributing {}".format(self.variable))

        for date_time in self.date_time:

            data = data_queue[self.variable].get(date_time)
            self.distribute(data)
            smrf_queue[self.variable].put([date_time, self.cloud_factor])
