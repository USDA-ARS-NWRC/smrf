
import numpy as np
import logging
import netCDF4 as nc
from smrf.distribute import image_data
from smrf.envphys import snow,storms,precip
from smrf.envphys.core import envphys_c
from smrf.utils import utils
import os


class ppt(image_data.image_data):
    """
    The :mod:`~smrf.distribute.precip.ppt` class allows for variable specific
    distributions that go beyond the base class.

    The instantaneous precipitation typically has a positive trend with
    elevation due to orographic effects. However, the precipitation
    distribution can be further complicated for storms that have isolated
    impact at only a few measurement locations, for example thunderstorms
    or small precipitation events. Some distirubtion methods may be better
    suited than others for capturing the trend of these small events with
    multiple stations that record no precipitation may have a negative impact
    on the distribution.

    The precipitation phase, or the amount of precipitation falling as rain or
    snow, can significantly alter the energy and mass balance of the snowpack,
    either leading to snow accumulation or inducing melt :cite:`Marks&al:1998`
    :cite:`Kormos&al:2014`. The precipitation phase and initial snow density
    estimated using a variety of models that can be set in the configuration
    file.

    For more information on the available models, checkout
    :mod:`~smrf.envphys.snow`.

    After the precipitation phase is calculated, the storm infromation can be
    determined. The spatial resolution for which storm definitions are applied
    is based on the snow model thats selected.

    The time since last storm is based on an accumulated precipitation mass
    threshold, the time elapsed since it last snowed, and the precipitation
    phase.  These factors determine the start and end time of a storm that
    has produced enough precipitation as snow to change the surface albedo.

    Args:
        pptConfig: The [precip] section of the configuration file
        time_step: The time step in minutes of the data, defaults to 60

    Attributes:
        config: configuration from [precip] section
        precip: numpy array of the precipitation
        percent_snow: numpy array of the percent of time step that was snow
        snow_density: numpy array of the snow density
        storm_days: numpy array of the days since last storm
        storm_total: numpy array of the precipitation mass for the storm
        last_storm_day: numpy array of the day of the last storm (decimal day)
        last_storm_day_basin: maximum value of last_storm day within the mask
            if specified
        min: minimum value of precipitation is 0
        max: maximum value of precipitation is infinite
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class
            :mod:`!smrf.distribute.precipitation.ppt` that specifies the
            ``units`` and ``long_name`` for creating the NetCDF output file.
        variable: 'precip'

    """

    variable = 'precip'

    # these are variables that can be output
    output_variables = {'precip': {
                                  'units': 'mm',
                                  'standard_name': 'precipitation_mass',
                                  'long_name': 'Precipitation mass'
                                  },
                        'percent_snow': {
                                  'units': '%',
                                  'standard_name': 'percent_snow',
                                  'long_name': 'Percent of precipitation as snow'
                                  },
                        'snow_density': {
                                  'units': 'kg/m3',
                                  'standard_name': 'snow_density',
                                  'long_name': 'Precipitation snow density'
                                  },
                        'storm_days': {
                                  'units': 'day',
                                  'standard_name': 'days_since_last_storm',
                                  'long_name': 'Days since the last storm'
                                  },
                        'storm_total': {
                                  'units': 'mm',
                                  'standard_name': 'precipitation_mass_storm',
                                  'long_name': 'Precipitation mass for the storm period'
                                  },
                        'last_storm_day': {
                                  'units': 'day',
                                  'standard_name': 'day_of_last_storm',
                                  'long_name': 'Decimal day of the last storm since Oct 1'
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

    def __init__(self, pptConfig, start_date, precip_temp_method, time_step=60):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)

        # check and assign the configuration
        self.getConfig(pptConfig)
        self.time_step = float(time_step)
        self.start_date = start_date

        self.precip_temp_method = self.config['precip_temp_method']

    def initialize(self, topo, data):

        self._logger.debug('Initializing distribute.precip')

        self._initialize(topo, data.metadata)
        self.percent_snow = np.zeros((topo.ny, topo.nx))
        self.snow_density = np.zeros((topo.ny, topo.nx))
        self.storm_days = np.zeros((topo.ny, topo.nx))
        self.storm_total = np.zeros((topo.ny, topo.nx))
        self.last_storm_day = np.zeros((topo.ny, topo.nx))
        self.dem = topo.dem

        # Assign storm_days array if given
        if self.config["storm_days_restart"] != None:
            self._logger.debug('Reading {} from {}'.format('storm_days', self.config['storm_days_restart']))
            f = nc.Dataset(self.config['storm_days_restart'],'r')

            if 'storm_days' in f.variables:
                time = f.variables['time'][:]
                t = f.variables['time']
                time = nc.num2date(t[:], t.getncattr('units'), t.getncattr('calendar'))

                # start at index of storm_days - 1
                time_ind = np.where(time == self.start_date)[0] - 1

                if not time_ind:
                    self._logger.warning('Invalid storm_days input! Setting to 0.0')
                    self.storm_days = np.zeros((topo.ny, topo.nx))

                else:
                    self.storm_days = f.variables['storm_days'][time_ind,:,:][0]
            else:
                self._logger.warning('Variable {} not in {}, setting to 0.0'.format('storm_days', self.config['storm_days_restart']))
                self.storm_days = np.zeros((topo.ny, topo.nx))

            f.close()


        self.ppt_threshold = self.config['storm_mass_threshold']

        # Time steps needed to end a storm definition
        self.time_to_end_storm = self.config['time_steps_to_end_storms']

        self.nasde_model = self.config['nasde_model']

        self._logger.info('''Using {0} for the new accumulated snow density model:  '''.format(self.nasde_model))

        if self.nasde_model == 'marks2017':

            self.storm_total = np.zeros((topo.ny, topo.nx))

            self.storms = []
            self.time_steps_since_precip = 0
            self.storming = False

            # Clip and adjust the precip data so that there is only precip
            # during the storm and ad back in the missing data to conserve mass
            data.precip = data.precip[self.stations]
            self.storms, storm_count = storms.tracking_by_station(data.precip,
                                                                  mass_thresh=self.ppt_threshold,
                                                                  steps_thresh=self.time_to_end_storm)
            self.corrected_precip = storms.clip_and_correct(data.precip,
                                                            self.storms,
                                                            stations = self.stations)
            # self._logger.debug('''Conservation of mass check (precip -
            #                     precip_clipped):\n{0}'''.format(
            #                         data.precip.sum() -
            #                         corrected_precip.sum()))
            if storm_count != 0:
                self._logger.info("Identified Storms:\n{0}".format(self.storms))
                self.storm_id = 0
                self._logger.info("Estimated number of storms: {0}".format(storm_count))

            else:
                if (data.precip.sum() > 0).any():
                    self.storm_id = np.nan
                    self._logger.warning("Zero events triggered a storm definition, None of the precip will be used in this run.")

        # if redistributing due to wind
        if self.config['distribute_drifts']:
            self._tbreak_file = nc.Dataset(self.config['tbreak_netcdf'], 'r')
            self.tbreak = self._tbreak_file.variables['tbreak'][:]
            self.tbreak_direction = self._tbreak_file.variables['direction'][:]
            self._tbreak_file.close()
            self._logger.debug('Read data from {}'
                               .format(self.config['tbreak_netcdf']))

            # get the veg values
            self.veg_type = topo.veg_type
            matching = [s for s in self.config.keys() if "veg_" in s]
            v = {}
            for m in matching:
                if m != 'veg_default':
                    ms = m.split('_')
                    v[ms[1]] = float(self.config[m])
            self.veg = v

        self.mask = topo.mask

    def distribute_precip(self, data):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        Soley distributes the precipitation data and does not calculate the
        other dependent variables
        """

        self._logger.debug('{} Distributing precip'.format(data.name))

        # only need to distribute precip if there is any
        data = data[self.stations]
        if data.sum() > 0:

            # distribute data and set the min/max
            self._distribute(data, zeros=None)
            self.precip = utils.set_min_max(self.precip, self.min, self.max)

        else:
            # make everything else zeros
            self.precip = np.zeros(self.storm_days.shape)


    def distribute_precip_thread(self, queue, data):
        """
        Distribute the data using threading and queue. All data is provided and
        ``distribute_precip_thread`` will go through each time step and call
        :mod:`smrf.distribute.precip.ppt.distribute_precip` then puts the
        distributed data into the queue for:

        * :py:attr:`precip`

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """

        for t in data.index:

            self.distribute_precip(data.loc[t])

            queue[self.variable].put([t, self.precip])



    def distribute(self, data, dpt, ta, time, wind, temp, az, dir_round_cell,
                   wind_speed, cell_maxus, mask=None):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        The following steps are taken when distributing precip, if there is
        precipitation measured:

        1. Distribute the instaneous precipitation from the measurement data
        2. Determine the distributed precipitation phase based on the
            precipitation temperature
        3. Calculate the storms based on the accumulated mass, time since last
            storm, and precipitation phase threshold


        Args:
            data: Pandas dataframe for a single time step from precip
            dpt: dew point numpy array that will be used for the precipitaiton
                temperature
            ta:     air temp numpy array
            time:   pass in the time were are currently on
            wind: station wind speed at time step
            temp:   station air temperature at time step
            mask:   basin mask to apply to the storm days for calculating the
                    last storm day for the basin
        """

        self._logger.debug('%s Distributing all precip' % data.name)
        # only need to distribute precip if there is any
        data = data[self.stations]

        if self.nasde_model == 'marks2017':
            #Adjust the precip for undercatchment
            if self.config['adjust_for_undercatch']:
                self._logger.debug('%s Adjusting precip for undercatch...' % data.name)
                self.corrected_precip.loc[time] = \
                    precip.adjust_for_undercatch(self.corrected_precip.loc[time],
                                                 wind,
                                                 temp,
                                                 self.config,
                                                 self.metadata)

            #Use the clipped and corrected precip
            self.distribute_for_marks2017(self.corrected_precip.loc[time],
                                          dpt,
                                          ta,
                                          time,
                                          mask=mask)

        else:
            #Adjust the precip for undercatchment
            if self.config['adjust_for_undercatch']:
                self._logger.debug('%s Adjusting precip for undercatch...' % data.name)
                data = precip.adjust_for_undercatch(data,
                                                    wind,
                                                    temp,
                                                    self.config,
                                                    self.metadata)

            self.distribute_for_susong1999(data, dpt, time, mask=mask)

        # redistribute due to wind to account for driftin
        if self.config['distribute_drifts']:
            self._logger.debug('%s Redistributing due to wind' % data.name)
            if np.any(dpt < 0.5):
                self.precip = precip.dist_precip_wind(self.precip, dpt, az, dir_round_cell,
                                            wind_speed, cell_maxus, self.tbreak,
                                            self.tbreak_direction, self.veg_type,
                                            self.veg, self.config)

    def distribute_for_marks2017(self, data, dpt, ta, time, mask=None):
        """
        Specialized distribute function for working with the new accumulated
        snow density model Marks2017 requires storm total and a corrected
        precipitation as to avoid precip between storms.
        """
        #self.corrected_precip # = data.mul(self.storm_correction)
        self.precip_temp = None

        if data.sum() > 0.0:
            # Check for time in every storm
            for i, s in self.storms.iterrows():
                storm_start = s['start']
                storm_end = s['end']

                if time >= storm_start and time <= storm_end:
                    # establish storm info
                    self.storm_id = i
                    storm = self.storms.iloc[self.storm_id]
                    self.storming = True
                    break
                else:
                    self.storming = False

            self._logger.debug("Storming? {0}".format(self.storming))
            self._logger.debug("Current Storm ID = {0}".format(self.storm_id))

            # distribute data and set the min/max
            self._distribute(data, zeros=None)
            self.precip = utils.set_min_max(self.precip, self.min, self.max)

            # calculate precip temperature#
            if self.precip_temp_method == 'wet_bulb':
                # initialize timestep wet_bulb
                wet_bulb = np.zeros_like(dpt, dtype=np.float64)
                # calculate wet_bulb
                envphys_c.cwbt(ta, dpt, self.dem,
                               wet_bulb, 0.01,
                               16)
                # # store last time step of wet_bulb
                # self.wet_bulb_old = wet_bulb.copy()
                # store in precip temp for use in precip
                self.precip_temp = wet_bulb
            else:
                self.precip_temp = dpt

            if time == storm_start:
                # Entered into a new storm period distribute the storm total
                self._logger.debug('{0} Entering storm #{1}'
                                   .format(data.name, self.storm_id+1))
                if self.precip_temp.min() < 2.0:
                    self._logger.debug('''Distributing Total Precip
                                        for Storm #{0}'''
                                       .format(self.storm_id+1))
                    self._distribute(storm[self.stations].astype(float),
                                     other_attribute='storm_total')
                    self.storm_total = utils.set_min_max(self.storm_total,
                                                         self.min,
                                                         self.max)

            if self.storming and self.precip_temp.min() < 2.0:
                self._logger.debug('''Calculating new snow density for
                                    storm #{0}'''.format(self.storm_id+1))
                # determine the precip phase and den
                snow_den, perc_snow = snow.calc_phase_and_density(self.precip_temp,
                                                                  self.precip,
                                                                  nasde_model=self.nasde_model)

            else:
                snow_den = np.zeros(self.precip.shape)
                perc_snow = np.zeros(self.precip.shape)

            # calculate decimal days since last storm
            self.storm_days = storms.time_since_storm_pixel(self.precip,
                                                     self.precip_temp,
                                                     perc_snow,
                                                     storming=self.storming,
                                                     time_step=self.time_step/60.0/24.0,
                                                     stormDays=self.storm_days,
                                                     mass=self.ppt_threshold)

        else:
            self.storm_days += self.time_step/60.0/24.0
            self.precip = np.zeros(self.storm_days.shape)
            perc_snow = np.zeros(self.storm_days.shape)
            snow_den = np.zeros(self.storm_days.shape)

        # save the model state
        self.percent_snow = perc_snow
        self.snow_density = snow_den

        # day of last storm, this will be used in albedo
        self.last_storm_day = utils.water_day(data.name)[0] - \
            self.storm_days - 0.001

        # get the time since most recent storm
        if mask is not None:
            self.last_storm_day_basin = np.max(mask * self.last_storm_day)
        else:
            self.last_storm_day_basin = np.max(self.last_storm_day)


    def distribute_for_susong1999(self, data, ppt_temp, time, mask=None):
        """
        Docs for susong1999
        """

        if data.sum() > 0:

            # distribute data and set the min/max
            self._distribute(data)
            # see if the mass threshold has been passed
            self.precip = utils.set_min_max(self.precip, self.min, self.max)

            # determine the precip phase and den
            snow_den, perc_snow = snow.calc_phase_and_density(ppt_temp,
                                                              self.precip,
                                                              nasde_model=self.nasde_model)

            # determine the time since last storm
            stormDays, stormPrecip = storms.time_since_storm(self.precip,
                                                             perc_snow,
                                                             time_step=self.time_step/60/24,
                                                             mass=self.ppt_threshold,
                                                             time=self.time_to_end_storm,
                                                             stormDays=self.storm_days,
                                                             stormPrecip=self.storm_total)

            # save the model state
            self.percent_snow = perc_snow
            self.snow_density = snow_den
            self.storm_days = stormDays
            self.storm_total = stormPrecip

        else:

            self.storm_days += self.time_step/60/24

            # make everything else zeros
            self.precip = np.zeros(self.storm_days.shape)
            self.percent_snow = np.zeros(self.storm_days.shape)
            self.snow_density = np.zeros(self.storm_days.shape)

        # day of last storm, this will be used in albedo
        self.last_storm_day = utils.water_day(data.name)[0] - \
            self.storm_days - 0.001

        # get the time since most recent storm
        if mask is not None:
            self.last_storm_day_basin = np.max(mask * self.last_storm_day)
        else:
            self.last_storm_day_basin = np.max(self.last_storm_day)


    def distribute_thread(self, queue, data, date, mask=None):
        """
        Distribute the data using threading and queue. All data is provided and
        ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.precip.ppt.distribute` then puts the distributed
        data into the queue for:

        * :py:attr:`percent_snow`

        * :py:attr:`snow_density`
        * :py:attr:`storm_days`
        * :py:attr:`last_storm_day_basin`

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """

        for t in data.precip.index:

            dpt = queue['dew_point'].get(t)
            ta = queue['air_temp'].get(t)
            # variables for wind redistribution
            az = queue['wind_direction'].get(t)
            wind_speed = queue['wind_speed'].get(t)
            flatwind = queue['flatwind'].get(t)
            dir_round_cell = queue['dir_round_cell'].get(t)
            cell_maxus = queue['cellmaxus'].get(t)

            self.distribute(data.precip.loc[t], dpt, ta, t, data.wind_speed.loc[t],data.air_temp.loc[t],
                            az, dir_round_cell, flatwind, cell_maxus, mask=mask)

            queue[self.variable].put([t, self.precip])

            queue['percent_snow'].put([t, self.percent_snow])

            queue['snow_density'].put([t, self.snow_density])

            queue['precip_temp'].put([t, self.precip_temp])

            queue['last_storm_day_basin'].put([t, self.last_storm_day_basin])

            queue['storm_days'].put([t, self.storm_days])

            queue['storm_total'].put([t, self.storm_total])
            if self.nasde_model == "marks2017":
                queue['storm_id'].put([t, self.storm_id])



    def post_processor(self, main_obj, threaded=False):

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

        #  #Open files
        #  pp_fname = os.path.join(main_obj.config['output']['out_location'], 'precip.nc')
        #  t_fname = os.path.join(main_obj.config['output']['out_location'], 'dew_point.nc')

        #  pds = Dataset(pp_fname,'r')
        #  tds = Dataset(t_fname,'r')
        pass

        # Create a queue

        # calc data

        # output

        # clean
