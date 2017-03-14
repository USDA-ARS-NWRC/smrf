__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-05"
__version__ = "0.1.1"

import numpy as np
import logging
from smrf.distribute import image_data
from smrf.envphys import snow
from smrf.envphys import storms

from smrf.utils import utils
# import matplotlib.pyplot as plt

class ppt(image_data.image_data):
    """
    The :mod:`~smrf.distribute.precip.ppt` class allows for variable specific distributions that
    go beyond the base class

    The instantaneous precipitation typically has a positive trend with elevation due to orographic
    effects. However, the precipitation distribution can be further complicated for storms that
    have isolated impact at only a few measurement locations, for example thunderstorms or small
    precipitation events. Some distirubtion methods may be better suited than others for
    capturing the trend of these small events with multiple stations that record no precipitation may
    have a negative impact on the distribution.

    The precipitation phase, or the amount of precipitation falling as rain or snow, can significantly
    alter the energy and mass balance of the snowpack, either leading to snow accumulation or inducing
    melt :cite:`Marks&al:1998` :cite:`Kormos&al:2014`. The precipitation phase and initial snow density are
    based on the precipitation temperature (the distributed dew point temperature) and are estimated
    after Susong et al (1999) :cite:`Susong&al:1999`. The table below shows the relationship to
    precipitation temperature:

    ========= ======== ============ ===============
    Min Temp  Max Temp Percent snow Snow density
    [deg C]   [deg C]  [%]          [kg/m^3]
    ========= ======== ============ ===============
    -Inf      -5       100          75
    -5        -3       100          100
    -3        -1.5     100          150
    -1.5      -0.5     100          175
    -0.5      0        75           200
    0         0.5      25           250
    0.5       Inf      0            0
    ========= ======== ============ ===============

    After the precipitation phase is calculated, the storm infromation at each pixel can be determined.
    The time since last storm is based on an accumulated precipitation mass threshold, the time elapsed
    since it last snowed, and the precipitation phase.  These factors determine the start and end time
    of a storm that has produced enough precipitation as snow to change the surface albedo.

    Args:
        pptConfig: The [precip] section of the configuration file
        time_step: The time step in minutes of the data, defaults to 60

    Attributes:
        config: configuration from [precip] section
        precip: numpy array of the precipitation
        percent_snow: numpy array of the percent of time step that was snow
        snow_density: numpy array of the snow density
        storm_days: numpy array of the days since last storm
        storm_precip: numpy array of the precipitaiton mass for the storm
        last_storm_day: numpy array of the day of the last storm (decimal day)
        last_storm_day_basin: maximum value of last_storm day within the mask if specified
        min: minimum value of precipitation is 0
        max: maximum value of precipitation is infinite
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class :mod:`!smrf.distribute.precipitation.ppt`
            that specifies the ``units`` and ``long_name`` for creating the NetCDF output file.
        variable: 'precip'

    """

    variable = 'precip'

    # these are variables that can be output
    output_variables = {'precip':{
                                  'units': 'mm',
                                  'long_name': 'precipitation_mass'
                                  },
                        'percent_snow':{
                                  'units': '%',
                                  'long_name': 'percent_snow'
                                  },
                        'snow_density':{
                                  'units': 'kg/m^3',
                                  'long_name': 'snow_density'
                                  },
                        'storm_days':{
                                  'units': 'decimal_day',
                                  'long_name': 'days_since_last_storm'
                                  },
                        'storm_precip':{
                                  'units': 'mm',
                                  'long_name': 'precipitation_mass_storm'
                                  },
                        'last_storm_day':{
                                  'units': 'decimal_day',
                                  'long_name': 'day_of_last_storm'
                                  },
                        }


    max = np.Inf
    min = 0
    def __init__(self, pptConfig, time_step=60):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        self.getConfig(pptConfig)
        self.time_step = float(time_step)

        self._logger.debug('Created distribute.air_temp')


    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls :mod:`smrf.distribute.image_data.image_data._initialize`.
        Preallocates the following class attributes to zeros:

        * :py:attr:`percent_snow`
        * :py:attr:`snow_density`
        * :py:attr:`storm_days`
        * :py:attr:`storm_precip`
        * :py:attr:`last_storm_day`

        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic data
                and infomation
            metadata: metadata Pandas dataframe containing the station metadata,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`
        """

        self._logger.debug('Initializing distribute.precip')

        self._initialize(topo, metadata)

        self.percent_snow = np.zeros((topo.ny, topo.nx))
        self.snow_density = np.zeros((topo.ny, topo.nx))
        self.storm_days = np.zeros((topo.ny, topo.nx))
        self.storm_precip = np.zeros((topo.ny, topo.nx))
        self.last_storm_day = np.zeros((topo.ny, topo.nx))
        self.storms = []
        self.hours_since_ppt=0
        self.storming = False
        #Note while we do idenfiy storms here the calculations do not require the storm info
        self.storm_dependent = False

    def distribute_precip(self, data):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        Soley distributes the precipitation data and does not calculate the other
        dependent variables
        """

        self._logger.debug('%s Distributing precip' % data.name)

        # only need to distribute precip if there is any
        data = data[self.stations]
        if data.sum() > 0:

            # distribute data and set the min/max
            self._distribute(data, zeros=None)
            self.precip = utils.set_min_max(self.precip, self.min, self.max)

        else:

            # make everything else zeros
            self.precip = np.zeros(self.storm_days.shape)


    def distribute(self, data, dpt, mask=None):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        The following steps are taken when distributing precip, if there is precipitation measured:

        1. Distribute the instaneous precipitation from the measurement data
        2. Determine the distributed precipitation phase based on the precipitation temperature
        3. Calculate the storms based on the accumulated mass, time since last storm, and precipitation phase threshold


        Args:
            data: Pandas dataframe for a single time step from precip
            dpt: dew point numpy array that will be used for the precipitaiton temperature
            mask: basin mask to apply to the storm days for calculating the last storm day for the basin
        """

        self._logger.debug('%s Distributing all precip' % data.name)
        # only need to distribute precip if there is any
        data = data[self.stations]
        if data.sum() > 0:
            # distribute data and set the min/max
            self._distribute(data, zeros=None)
            self.precip = utils.set_min_max(self.precip, self.min, self.max)
            self.storming = storms.tracking(self.precip, data.name, self.storms, self.hours_since_ppt)
            self.hours_since_ppt = 0

            # determine the precip phase
            perc_snow, snow_den = snow.mkprecip(self.precip, dpt)

            # determine the time since last storm
            stormDays, stormPrecip = storms.time_since_storm(self.precip, perc_snow,
                                                        time_step=self.time_step/60/24, mass=0.5, time=4,
                                                        stormDays=self.storm_days,
                                                        stormPrecip=self.storm_precip)

            # save the model state
            self.percent_snow = perc_snow
            self.snow_density = snow_den
            self.storm_days = stormDays
            self.storm_precip = stormPrecip

        else:
            self.hours_since_ppt+=1

            self.storm_days += self.time_step/60/24

            # make everything else zeros
            self.precip = np.zeros(self.storm_days.shape)
            self.percent_snow = np.zeros(self.storm_days.shape)
            self.snow_density = np.zeros(self.storm_days.shape)


        # day of last storm, this will be used in albedo
        self.last_storm_day = utils.water_day(data.name)[0] - self.storm_days - 0.001

        # get the time since most recent storm
        if mask is not None:
            self.last_storm_day_basin = np.max(mask * self.last_storm_day)
        else:
            self.last_storm_day_basin = np.max(self.last_storm_day)

    def distribute_thread(self, queue, data, mask=None):
        """
        Distribute the data using threading and queue. All data is provided and ``distribute_thread``
        will go through each time step and call :mod:`smrf.distribute.precip.ppt.distribute` then
        puts the distributed data into the queue for:

        * :py:attr:`percent_snow`
        * :py:attr:`snow_density`
        * :py:attr:`storm_days`
        * :py:attr:`last_storm_day_basin`

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """

        for t in data.index:

            dpt = queue['dew_point'].get(t)

            self.distribute(data.ix[t], dpt, mask)

#             self._logger.debug('Putting %s -- %s' % (t, 'precip'))
            queue[self.variable].put( [t, self.precip] )

#             self._logger.debug('Putting %s -- %s' % (t, 'percent_snow'))
            queue['percent_snow'].put( [t, self.percent_snow] )

#             self._logger.debug('Putting %s -- %s' % (t, 'snow_density'))
            queue['snow_density'].put( [t, self.snow_density] )

#             self._logger.debug('Putting %s -- %s' % (t, 'last_storm_day_basin'))
            queue['last_storm_day_basin'].put( [t, self.last_storm_day_basin] )

#             self._logger.debug('Putting %s -- %s' % (t, 'storm_days'))
            queue['storm_days'].put( [t, self.storm_days] )

    def post_processor(self):
        """

        """
        pass
