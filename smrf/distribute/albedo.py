import numpy as np

from smrf.distribute import image_data
from smrf.envphys import albedo
from smrf.utils import utils


class Albedo(image_data.image_data):
    """
    The :mod:`~smrf.distribute.albedo.Albedo` class allows for variable
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
    """

    variable = 'albedo'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
        'albedo_vis': {
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

    BASE_THREAD_VARIABLES = frozenset([
        'albedo_vis',
        'albedo_ir'
    ])

    def __init__(self, albedoConfig):
        """
        Initialize albedo()

        Args:
            albedoConfig: configuration from [albedo] section
        """

        # extend the base class
        image_data.image_data.__init__(self, self.variable)

        # Get the veg values for the decay methods. Date method uses self.veg
        # Hardy2000 uses self.litter
        for d in ['veg', 'litter']:
            v = {}

            matching = [s for s in albedoConfig.keys()
                        if "{0}_".format(d) in s]
            for m in matching:
                ms = m.split('_')
                v[ms[-1]] = albedoConfig[m]

            # Create self.litter,self.veg
            setattr(self, d, v)

        self.getConfig(albedoConfig)

        self._logger.debug('Created distribute.albedo')

    def initialize(self, topo, data, date_time=None):
        """
        Initialize the distribution, calls image_data.image_data._initialize()

        Args:
            topo: smrf.data.loadTopo.Topo instance contain topo data/info
            data: data dataframe containing the station data

        """

        self._logger.debug('Initializing distribute.albedo')
        self.veg_type = topo.veg_type
        self.date_time = date_time
        self._initialize(topo, data.metadata)

        if self.config["decay_method"] is None:
            self._logger.warning("No decay method is set!")

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

            alb_v, alb_ir = albedo.albedo(
                storm_day, cosz,
                self.config['grain_size'],
                self.config['max_grain'],
                self.config['dirt'])

            # Perform litter decay
            if self.config['decay_method'] == 'date_method':
                alb_v_d, alb_ir_d = albedo.decay_alb_power(
                    self.veg,
                    self.veg_type,
                    self.config['date_method_start_decay'],
                    self.config['date_method_end_decay'],
                    current_time_step,
                    self.config['date_method_decay_power'],
                    alb_v, alb_ir)

                alb_v = alb_v_d
                alb_ir = alb_ir_d

            elif self.config['decay_method'] == 'hardy2000':
                alb_v_d, alb_ir_d = albedo.decay_alb_hardy(
                    self.litter,
                    self.veg_type,
                    storm_day,
                    alb_v,
                    alb_ir)

                alb_v = alb_v_d
                alb_ir = alb_ir_d

            self.albedo_vis = utils.set_min_max(alb_v, self.min, self.max)
            self.albedo_ir = utils.set_min_max(alb_ir, self.min, self.max)

        else:
            self.albedo_vis = np.zeros(storm_day.shape)
            self.albedo_ir = np.zeros(storm_day.shape)

    def distribute_thread(self, smrf_queue, data_queue=None):
        """
        Distribute the data using threading and queue

        Args:
            queue: queue dict for all variables
            date: dates to loop over

        Output:
            Changes the queue albedo_vis, albedo_ir
                for the given date
        """
        self._logger.info("Distributing {}".format(self.variable))

        for date_time in self.date_time:

            illum_ang = smrf_queue['illum_ang'].get(date_time)
            storm_day = smrf_queue['storm_days'].get(date_time)

            self.distribute(date_time, illum_ang, storm_day)

            smrf_queue['albedo_vis'].put([date_time, self.albedo_vis])
            smrf_queue['albedo_ir'].put([date_time, self.albedo_ir])
