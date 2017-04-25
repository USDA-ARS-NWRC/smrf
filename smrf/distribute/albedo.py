__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-06"
__version__ = "0.1.1"

import numpy as np
import logging
from smrf.distribute import image_data
from smrf.envphys import radiation
# import smrf.utils as utils
# import matplotlib.pyplot as plt

class albedo(image_data.image_data):
    """
    The :mod:`~smrf.distribute.albedo.albedo` class allows for variable specific distributions that
    go beyond the base class

    The visible (280-700nm) and infrared (700-2800nm) albedo follows the relationships described in
    Marks et al. (1992) :cite:`Marks&al:1992`. The albedo is a function of the time since last storm,
    the solar zenith angle, and grain size. The time since last storm is tracked on a pixel by pixel
    basis and is based on where there is significant accumulated distributed precipitation. This allows
    for storms to only affect a small part of the basin and have the albedo decay at different rates
    for each pixel.

    Args:
        albedoConfig: The [albedo] section of the configuration file

    Attributes:
        albedo_vis: numpy array of the visible albedo
        albedo_ir: numpy array of the infrared albedo
        config: configuration from [albedo] section
        min: minimum value of albedo is 0
        max: maximum value of albedo is 1
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class :mod:`!smrf.distribute.albedo.albedo`
            that specifies the ``units`` and ``long_name`` for creating the NetCDF output file.
        variable: 'albedo'
    """

    variable = 'albedo'
    min = 0
    max = 1

    # these are variables that can be output
    output_variables = {'albedo_vis': {
                                       'units': 'None',
                                       'long_name': 'visible_albedo'
                                       },
                        'albedo_ir': {
                                       'units': 'None',
                                       'long_name': 'infrared_albedo'
                                       }
                        }
    # these are variables that are operate at the end only and do not need to be written during main distribute loop
    post_process_variables = {}

    def __init__(self, albedoConfig):
        """
        Initialize albedo()

        Args:
            albedoConfig: configuration from [albedo] section
        """

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        if 'grain_size' not in albedoConfig:
            albedoConfig['grain_size'] = 300
        else:
            albedoConfig['grain_size'] = float(albedoConfig['grain_size'])

        if 'max_grain' not in albedoConfig:
            albedoConfig['max_grain'] = 2000
        else:
            albedoConfig['max_grain'] = float(albedoConfig['max_grain'])

        if 'dirt' not in albedoConfig:
            albedoConfig['dirt'] = 2.0
        else:
            albedoConfig['dirt'] = float(albedoConfig['dirt'])

        self.config = albedoConfig

        self._logger.debug('Created distribute.albedo')


    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()

        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata

        """

#         self._initialize(topo, metadata)
        self._logger.debug('Initializing distribute.albedo')


    def distribute(self, current_time_step, cosz, storm_day):
        """
        Distribute air temperature given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        Args:
            current_time_step: Current time step in datetime object
            cosz: numpy array of the illumination angle for the current time step
            storm_day: numpy array of the decimal days since it last
                snowed at a grid cell

        """

        self._logger.debug('%s Distributing albedo' % current_time_step)

        # only need to calculate albedo if the sun is up
        if cosz is not None:

            alb_v, alb_ir = radiation.albedo(storm_day, cosz,
                                             self.config['grain_size'],
                                             self.config['max_grain'],
                                             self.config['dirt'])

            self.albedo_vis = alb_v
            self.albedo_ir = alb_ir

        else:
            self.albedo_vis = np.zeros(storm_day.shape)
            self.albedo_ir = np.zeros(storm_day.shape)



    def distribute_thread(self, queue, date):
        """
        Distribute the data using threading and queue

        Args:
            queue: queue dict for all variables
            date: dates to loop over

        Output:
            Changes the queue albedo_vis, albedo_ir
                for the given date
        """

        for t in date:

            illum_ang = queue['illum_ang'].get(t)
            storm_day = queue['storm_days'].get(t)

            self.distribute(t, illum_ang, storm_day)

            self._logger.debug('Putting %s -- %s' % (t, 'albedo_vis'))
            queue['albedo_vis'].put( [t, self.albedo_vis] )

            self._logger.debug('Putting %s -- %s' % (t, 'albedo_ir'))
            queue['albedo_ir'].put( [t, self.albedo_ir] )
