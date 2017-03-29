__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-07"
__version__ = "0.1.1"

import numpy as np
import logging
from smrf.distribute import image_data

class ts(image_data.image_data):
    """
    The :mod:`~smrf.distribute.soil_temp.ts` class allows for variable specific distributions that
    go beyond the base class.

    Soil temperature is simply set to a constant value during initialization.  If soil temperature
    measurements are available, the values can be distributed using the distribution methods.

    Args:
        soilConfig: The [soil] section of the configuration file
        tempDir: location of temp/working directory (default=None)

    Attributes:
        config: configuration from [soil] section
        soil_temp: numpy array of the soil temperature
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class :mod:`!smrf.distribute.soil_temp.ts`
            that specifies the ``units`` and ``long_name`` for creating the NetCDF output file.
        variable: 'soil_temp'

    """

    variable = 'soil_temp'

    # these are variables that can be output
    output_variables = {'soil_temp': {
                                  'units': 'degree Celcius',
                                  'long_name': 'soil_temperature'
                                  }
                        }

    def __init__(self, soilConfig, tempDir=None):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        self.config = soilConfig

        self._logger.debug('Created distribute.soil_temp')


    def initialize(self, topo, metadata):
        """
        Initialize the distribution and set the soil temperature to a constant value
        based on the configuration file.

        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic data
                and infomation
            metadata: metadata Pandas dataframe containing the station metadata,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        """

        self._logger.debug('Initializing distribute.soil_temp')
#         self._initialize(topo, metadata)
        self.soil_temp = float(self.config['temp']) * np.ones(topo.dem.shape)


    def distribute(self):
        """
        No distribution is performed on soil temperature at the moment, method simply
        passes.

        Args:
            None
        """

#         self._logger.debug('Distributing soil temp')
        pass
