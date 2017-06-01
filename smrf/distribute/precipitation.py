__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-05"
__version__ = "0.2.2"

import numpy as np
import os
from datetime import datetime
import logging
from netCDF4 import Dataset
from smrf.distribute import image_data
from smrf.envphys import snow
from smrf.envphys import storms

from smrf.utils import utils
import pytz
import timeit

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
    melt :cite:`Marks&al:1998` :cite:`Kormos&al:2014`. The precipitation phase and initial snow density
    estimated using a variety of models that can be set in the configuration file.

    For more information on the available models, checkout :mod:`~smrf.envphys.snow`.

    After the precipitation phase is calculated, the storm infromation can be determined. The spatial
    resolution for which storm definitions are applied is based on the snow model thats selected.

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
        storm_precip: numpy array of the precipitation mass for the storm
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
        # these are variables that are operate at the end only and do not need to be written during main distribute loop
    post_process_variables = { }

    max = np.Inf
    min = 0

    def __init__(self, pptConfig, time_step=60):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        self.getConfig(pptConfig)
        self.time_step = float(time_step)

    def initialize(self, topo, data):

        self._logger.debug('Initializing distribute.precip')

        self._initialize(topo, data.metadata)
        self.percent_snow = np.zeros((topo.ny, topo.nx))
        self.snow_density = np.zeros((topo.ny, topo.nx))
        self.storm_days = np.zeros((topo.ny, topo.nx))
        self.storm_precip = np.zeros((topo.ny, topo.nx))
        self.last_storm_day = np.zeros((topo.ny, topo.nx))
        self.storm_total = np.zeros((topo.ny, topo.nx))

        self.storms = []
        self.time_steps_since_precip = 0
        self.storming = False

        if 'storm_mass_thresh' in self.config:
            self.ppt_threshold = self.config['storm_mass_thresh']
        else:
            self.ppt_threshold = 0.1 #mm
        if 'time_steps_to_end_storms' in self.config:
            self.time_to_end_storm = self.config['time_steps_to_end_storms']
        else:
                self.time_to_end_storm = 2 # Time steps it take to end a storm definition

        if 'nasde_model' in self.config:
            self.nasde_model= self.config['nasde_model']
        else:
            self.nasde_model = 'susong1999'

        if self.nasde_model == 'marks2017':
            #Clip and adjust the precip data so that there is only precip during the storm
            # and ad back in the missing data to conserve mass.
            self.storms, storm_count = storms.tracking_by_station(data.precip, mass_thresh = self.ppt_threshold, steps_thresh = self.time_to_end_storm)
            self.corrected_precip = storms.clip_and_correct(data.precip,self.storms)
            self._logger.debug("Conservation of mass check (precip - precip_clipped):\n{0}".format(data.precip.sum() - self.corrected_precip.sum()))

            self._logger.info("Identified Storms:\n{0}".format(self.storms))
            self.storm_id = 0
            self._logger.info("Estimated number of storms: {0}".format(storm_count))


        self._logger.info("Using {0} for the new accumulated snow density model:  ".format(self.nasde_model))

    def distribute_precip(self, data):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        Soley distributes the precipitation data and does not calculate the other
        dependent variables
        """

        self._logger.debug('{} Distributing precip'.format(data.name))

        # only need to distribute precip if there is any
        data = data[self.stations]
        if self.corrected_precip[data.name].sum() > 0:

            # distribute data and set the min/max
            self._distribute(self.corrected_precip[data.name], zeros=None)
            self.precip = utils.set_min_max(self.precip, self.min, self.max)

        else:
            # make everything else zeros
            self.precip = np.zeros(self.storm_days.shape)


    def distribute_precip_thread(self,  queue, data):
        """
        Distribute the data using threading and queue. All data is provided and ``distribute_precip_thread``
        will go through each time step and call :mod:`smrf.distribute.precip.ppt.distribute_precip` then
        puts the distributed data into the queue for:

        * :py:attr:`precip`

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """

        for t in data.index:

            self.distribute_precip(data.ix[t])

            queue[self.variable].put( [t, self.precip] )

    def distribute(self, data, dpt, time, mask=None):
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
            time: pass in the time were are currently on
            mask: basin mask to apply to the storm days for calculating the last storm day for the basin
        """

        self._logger.debug('%s Distributing all precip' % data.name)
        # only need to distribute precip if there is any
        data = data[self.stations]


        if self.nasde_model == 'marks2017':
            self.distribute_for_marks2017(data,dpt,time,mask=mask)

        else:
            if data.sum() > 0:

                # distribute data and set the min/max
                self._distribute(data, zeros=None)
                self.precip = utils.set_min_max(self.precip, self.min, self.max)

                # remove very small precipitation

                # determine the precip phase and den
                snow_den, perc_snow = snow.calc_phase_and_density(dpt,self.precip, nasde_model=self.nasde_model)

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


    def distribute_for_marks2017(self, data, dpt, time, mask=None):
        '''
        Specialized distribute function for working with the new accumulated snow
        density model Marks2017 requires storm total  and a corrected precipitation
        as to avoid precip between storms.

        '''

        if self.corrected_precip.ix[time].sum() > 0:

            #Check for time in every storm
            for i,s in self.storms.iterrows():
                if time >= s['start'] and time <= s['end']:
                    #establish storm info
                    self.storm_id = i
                    storm = self.storms.iloc[self.storm_id]
                    storm_start = s['start']
                    storm_end = s['end']
                    self.storming = True
                    self._logger.debug("Current Storm ID = {0}".format(self.storm_id))
                    self._logger.debug("Storming? {0}".format(self.storming))
                    self._logger.debug("During storm time? {0}".format(time >= storm_start and time <= storm_end))

                    break
                else:
                    self.storming  = False

            # distribute data and set the min/max
            self._distribute(self.corrected_precip.ix[time], zeros=None)
            self.precip = utils.set_min_max(self.precip, self.min, self.max)

            if time == storm_start:
                #Entered into a new storm period distribute the storm total
                self._logger.debug('{0} Entering storm #{1}'.format(data.name,self.storm_id+1))
                if dpt.min() < 2.0:
                    self._logger.debug(' Distributing Total Precip for Storm #{0}'.format(self.storm_id+1))
                    self._distribute(storm[self.stations].astype(float),
                                     other_attribute='storm_total')
                    self.storm_total = utils.set_min_max(self.storm_total, self.min, self.max)

            #During a storm we only need to calc density but not distribute storm total as well as when it is cold enough.
            # TODO calculating the snow density is only needed once per storm, so some speedup could be had there as well
            if self.storming and dpt.min() < 2.0:
                self._logger.debug('Calculating new snow density for storm #{0}'.format(self.storm_id+1))
                # determine the precip phase and den
                snow_den, perc_snow = snow.calc_phase_and_density(dpt, self.precip, nasde_model=self.nasde_model)

            else:
                snow_den = np.zeros(self.precip.shape)
                perc_snow = np.zeros(self.precip.shape)

        else:
            #self.storm_days += self.time_step/60/24
            self.precip = np.zeros(self.storm_days.shape)
            perc_snow = np.zeros(self.storm_days.shape)
            snow_den = np.zeros(self.storm_days.shape)

        # determine time since last storm basin wide
        stormDays = storms.time_since_storm_basin(self.precip, self.storms.iloc[self.storm_id],
                                                    self.storm_id, self.storming, time, time_step=self.time_step/60/24, stormDays=self.storm_days)

        self.storm_days = stormDays

        # save the model state
        self.percent_snow = perc_snow
        self.snow_density = snow_den

        # day of last storm, this will be used in albedo
        self.last_storm_day = utils.water_day(data.name)[0] - self.storm_days - 0.001

        # get the time since most recent storm
        if mask is not None:
            self.last_storm_day_basin = np.max(mask * self.last_storm_day)
        else:
            self.last_storm_day_basin = np.max(self.last_storm_day)

    def distribute_thread(self, queue, data, date, mask=None):
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

        #for t,time in enumerate(date):
        for t in data.index:

            dpt = queue['dew_point'].get(t)

            #self.distribute(data.ix[t], dpt, time, mask = mask)
            self.distribute(data.ix[t], dpt, t, mask = mask)

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

            if self.nasde_model == "marks2017":
                queue['storm_id'].put( [t, self.storm_id])

                queue['storm_total'].put( [t, self.storm_total])


    def post_process_snow_density(self, main_obj, pds, tds, storm):
        """
        Calculates the snow density for a single storm.

        Arguments:
            main_obj - the main smrf obj running everything
            pds - netcdf object containing precip data
            tds - netcdf object containing temp data
            storm - a dictionary containing the start and end values of the storm.
                    A single entry from the storm lst

        returns: None, stores self.snow_density
        """

        storm_accum = np.zeros(pds.variables['precip'][0].shape)

        delta  = (storm['end']- storm['start'])

        storm_span = delta.total_seconds()/(60.0*self.time_step)
        self._logger.debug("Storm Duration = {0} hours".format(storm_span))

        start = main_obj.date_time.index(storm['start'])
        end = main_obj.date_time.index(storm['end'])

        storm_time = main_obj.date_time[start:end]

        for t in storm_time:
            i  = main_obj.date_time.index(t)
            storm_accum +=pds.variables['precip'][i][:][:]

        #self._logger.debug("Calculating snow density...")
        for t in storm_time:
            i  = main_obj.date_time.index(t)
            dpt = tds.variables['dew_point'][i]

            #self._logger.debug("Calculating snow density at {0}".format(t))
            self.snow_density = snow.calc_phase_and_density(storm_accum, dpt)

            main_obj.output(t, module = 'precip', out_var = 'snow_density')

    def post_processor(self,main_obj, threaded = False):
        """
        Process the snow density values
        """
        pass
        #
        # self._logger.info("Estimated total number of storms: {0} ...".format(len(self.storms)))
        #
        # #Open files
        # pp_fname = os.path.join(main_obj.config['output']['out_location'], 'precip.nc')
        # t_fname = os.path.join(main_obj.config['output']['out_location'], 'dew_point.nc')
        #
        # pds = Dataset(pp_fname,'r')
        # tds = Dataset(t_fname,'r')
        #
        # #Calculate the start of the simulation from file for calculating count
        # sim_start = (datetime.strptime((pds.variables['time'].units.split('since')[-1]).strip(),'%Y-%m-%d %H:%S'))
        # self._logger.debug("There were {0} total storms during this run".format(len(self.storms)))
        #
        #
        # #Cycle through all the storms
        # for i,storm in enumerate(self.storms):
        #     self._logger.debug("Calculating snow density for Storm #{0}".format(i+1))
        #     self.post_process_snow_density(main_obj,pds,tds,storm)
        #
        # pds.close()
        # tds.close()

    def post_processor_threaded(self, main_obj):
        #  self._logger.info("Post processing snow_density...")
         #
        #  #Open files
        #  pp_fname = os.path.join(main_obj.config['output']['out_location'], 'precip.nc')
        #  t_fname = os.path.join(main_obj.config['output']['out_location'], 'dew_point.nc')
         #
        #  pds = Dataset(pp_fname,'r')
        #  tds = Dataset(t_fname,'r')
        pass


        #Create a queue

        #calc data

        #output

        #clean
