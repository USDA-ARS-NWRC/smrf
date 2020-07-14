import numpy as np

from smrf.distribute import image_data


class ts(image_data.image_data):
    """
    The :mod:`~smrf.distribute.soil_temp.ts` class allows for variable specific
    distributions that go beyond the base class.

    Soil temperature is simply set to a constant value during initialization.
    If soil temperature measurements are available, the values can be
    distributed using the distribution methods.

    Args:
        soilConfig: The [soil] section of the configuration file

    Attributes:
        config: configuration from [soil] section
        soil_temp: numpy array of the soil temperature
        stations: stations to be used in alphabetical order

    """

    variable = 'soil_temp'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
        'soil_temp': {
            'units': 'degree_Celcius',
            'standard_name': 'soil_temperature',
            'long_name': 'Soil temperature'
        }
    }

    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    def __init__(self, soilConfig):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)

        self.config = soilConfig

        self._logger.debug('Created distribute.soil_temp')

    def initialize(self, topo, data, date_time=None):
        """
        Initialize the distribution and set the soil temperature to a constant
        value based on the configuration file.

        Args:
            topo: :mod:`smrf.data.loadTopo.Topo` instance contain topographic
                data and infomation
            metadata: data Pandas dataframe containing the station data,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.soil_temp')
        self.date_time = date_time
#         self._initialize(topo, metadata)
        self.soil_temp = float(self.config['temp']) * np.ones(topo.dem.shape)

    def distribute(self):
        """
        No distribution is performed on soil temperature at the moment, method
        simply passes.

        Args:
            None
        """

#         self._logger.debug('Distributing soil temp')
        pass
