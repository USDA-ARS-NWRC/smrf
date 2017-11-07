import numpy as np
import logging
import pandas as pd
import datetime
import pytz
from smrf.distribute import image_data
from smrf.envphys import radiation
from smrf.utils import utils

class albedo(image_data.image_data):
    """
    The :mod:`~smrf.distribute.albedo.albedo` class allows for variable
    specific distributions that go beyond the base class.

    The visible (280-700nm) and infrared (700-2800nm) albedo follows the
    relationships described in Marks et al. (1992) :cite:`Marks&al:1992`. The
    albedo is a function of the time since last storm, the solar zenith angle,
    and grain size. The time since last storm is tracked on a pixel by pixel
    basis and is based on where there is significant accumulated distributed
    precipitation. This allows for storms to only affect a small part of the
    basin and have the albedo decay at different rates for each pixel.

    Args:
        albedoConfig: The [albedo] section of the configuration file

    Attributes:
        albedo_vis: numpy array of the visible albedo
        albedo_ir: numpy array of the infrared albedo
        config: configuration from [albedo] section
        min: minimum value of albedo is 0
        max: maximum value of albedo is 1
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class
            :mod:`!smrf.distribute.albedo.albedo` that specifies the ``units``
            and ``long_name`` for creating the NetCDF output file.
        variable: 'albedo'
    """

    variable = 'albedo'

    # these are variables that can be output
    output_variables = {'albedo_vis': {
                                       'units': 'None',
                                       'standard_name': 'visible_albedo',
                                       'long_name': 'Visible wavelength albedo'
                                       },
                        'albedo_ir': {
                                       'units': 'None',
                                       'standard_name': 'infrared_albedo',
                                       'long_name': 'Infrared wavelength albedo'
                                       }
                        }
    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
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

        #Get the veg values for the decay methods. Date method uses self.veg
        #Hardy2000 uses self.litter
        for d in ['veg','litter']:
            v = {}

            matching = [s for s in albedoConfig.keys() if "{0}_".format(d) in s]
            for m in matching:
                ms = m.split('_')
                v[ms[1]] = albedoConfig[m]

            #create self.litter,self.veg
            setattr(self,d,v)

        #Add time zone
        self.config = albedoConfig
        self.min = self.config['min']
        self.max = self.config['max']

        self._logger.debug('Created distribute.albedo')

    def initialize(self, topo, data):
        """
        Initialize the distribution, calls image_data.image_data._initialize()

        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            data: data dataframe containing the station data

        """

#         self._initialize(topo, metadata)
        self._logger.debug('Initializing distribute.albedo')
        self.veg_type = topo.veg_type

    def distribute(self, current_time_step, cosz, storm_day):
        """
        Distribute air temperature given a Panda's dataframe for a single time
        step. Calls :mod:`smrf.distribute.image_data.image_data._distribute`.

        Args:
            current_time_step: Current time step in datetime object
            cosz: numpy array of the illumination angle for the current time
                step
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

            # Perform litter decay
            if self.config['decay_method'] == 'date_method':
                if (self.config['start_decay'] is not None and
                        self.config['end_decay'] is not None and
                        self.config['end_decay'] > self.config['start_decay']):

                    alb_v_d, alb_ir_d = radiation.decay_alb_power(self.veg,
                                            self.veg_type,
                                            self.config['start_decay'],
                                            self.config['end_decay'],
                                            current_time_step,
                                            self.config['decay_power'], alb_v, alb_ir)
                    alb_v = alb_v_d
                    alb_ir = alb_ir_d
                else:
                    self._logger.error('Need correct inputs for decay method: {0}'.format(self.config['decay_method']))

            elif self.config['decay_method'] == 'hardy2000':
                alb_v_d, alb_ir_d = radiation.decay_alb_hardy(self.litter,
                                                              self.veg_type,
                                                              storm_day,
                                                              alb_v,
                                                              alb_ir)
                alb_v = alb_v_d
                alb_ir = alb_ir_d

            self.albedo_vis = utils.set_min_max(alb_v,self.min,self.max)
            self.albedo_ir = utils.set_min_max(alb_ir,self.min,self.max)

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
            queue['albedo_vis'].put([t, self.albedo_vis])

            self._logger.debug('Putting %s -- %s' % (t, 'albedo_ir'))
            queue['albedo_ir'].put([t, self.albedo_ir])
