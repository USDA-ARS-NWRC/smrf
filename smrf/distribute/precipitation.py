
import netCDF4 as nc
import numpy as np

from smrf.distribute import image_data
from smrf.envphys import precip, snow, storms
from smrf.utils import utils


class ppt(image_data.image_data):
    """
    The :mod:`~smrf.distribute.precip.ppt` class allows for variable specific
    distributions that go beyond the base class.

    The instantaneous precipitation typically has a positive trend with
    elevation due to orographic effects. However, the precipitation
    distribution can be further complicated for storms that have isolated
    impact at only a few measurement locations, for example thunderstorms
    or small precipitation events. Some distribution methods may be better
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

    After the precipitation phase is calculated, the storm information can be
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
        min: minimum value of precipitation is 0
        max: maximum value of precipitation is infinite
        stations: stations to be used in alphabetical order

    """

    variable = 'precip'

    # these are variables that can be output
    OUTPUT_VARIABLES = {
        'precip': {
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
        }
    }

    # these are variables that are operate at the end only and do not need to
    # be written during main distribute loop
    post_process_variables = {}

    BASE_THREAD_VARIABLES = frozenset([
        'precip',
        'percent_snow',
        'snow_density',
        'storm_days',
        'storm_total'
    ])

    def __init__(self, pptConfig, start_date, time_step=60):

        # extend the base class
        image_data.image_data.__init__(self, self.variable)

        # check and assign the configuration
        self.getConfig(pptConfig)
        self.time_step = float(time_step)
        self.start_date = start_date

    def initialize(self, topo, data, date_time=None):

        self._logger.debug('Initializing distribute.precip')

        self.date_time = date_time
        self._initialize(topo, data.metadata)
        self.percent_snow = np.zeros((topo.ny, topo.nx))
        self.snow_density = np.zeros((topo.ny, topo.nx))
        self.storm_days = np.zeros((topo.ny, topo.nx))
        self.storm_total = np.zeros((topo.ny, topo.nx))
        self.last_storm_day = np.zeros((topo.ny, topo.nx))
        self.dem = topo.dem

        # Assign storm_days array if given
        if self.config["storm_days_restart"] is not None:
            self._logger.debug('Reading {} from {}'.format(
                'storm_days', self.config['storm_days_restart']))
            f = nc.Dataset(self.config['storm_days_restart'], 'r')

            if 'storm_days' in f.variables:
                time = f.variables['time'][:]
                t = f.variables['time']
                time = nc.num2date(t[:], t.getncattr(
                    'units'), t.getncattr('calendar'))

                # start at index of storm_days - 1
                time_ind = np.where(time == self.start_date)[0] - 1

                if not time_ind:
                    self._logger.warning(
                        'Invalid storm_days input! Setting to 0.0')
                    self.storm_days = np.zeros((topo.ny, topo.nx))

                else:
                    self.storm_days = f.variables['storm_days'][time_ind, :, :][0]  # noqa
            else:
                self._logger.warning(
                    'Variable {} not in {}, setting to 0.0'.format(
                        'storm_days', self.config['storm_days_restart']))
                self.storm_days = np.zeros((topo.ny, topo.nx))

            f.close()

        self.ppt_threshold = self.config['storm_mass_threshold']

        # Time steps needed to end a storm definition
        self.time_to_end_storm = self.config['marks2017_timesteps_to_end_storms']  # noqa

        self.nasde_model = self.config['new_snow_density_model']

        self._logger.info(
            """Using {0} for the new accumulated snow density"""
            """ model:  """.format(self.nasde_model))

        if self.nasde_model == 'marks2017':
            self.add_thread_variables('storm_id')

            self.storm_total = np.zeros((topo.ny, topo.nx))

            self.storms = []
            self.time_steps_since_precip = 0
            self.storming = False

            # Clip and adjust the precip data so that there is only precip
            # during the storm and ad back in the missing data to conserve mass
            data.precip = data.precip[self.stations]
            self.storms, storm_count = storms.tracking_by_station(
                data.precip,
                mass_thresh=self.ppt_threshold,
                steps_thresh=self.time_to_end_storm)
            self.corrected_precip = storms.clip_and_correct(
                data.precip,
                self.storms,
                stations=self.stations)

            if storm_count != 0:
                self._logger.info(
                    "Identified Storms:\n{0}".format(self.storms))
                self.storm_id = 0
                self._logger.info(
                    "Estimated number of storms: {0}".format(storm_count))

            else:
                if (data.precip.sum() > 0).any():
                    self.storm_id = np.nan
                    self._logger.warning("Zero events triggered a storm "
                                         " definition, None of the precip will"
                                         " be used in this run.")

        # if redistributing due to wind
        if self.config['precip_rescaling_model'] == 'winstral':
            self._tbreak_file = nc.Dataset(
                self.config['winstral_tbreak_netcdf'], 'r')
            self.tbreak = self._tbreak_file.variables['tbreak'][:]
            self.tbreak_direction = self._tbreak_file.variables['direction'][:]
            self._tbreak_file.close()
            self._logger.debug('Read data from {}'
                               .format(self.config['winstral_tbreak_netcdf']))

            # get the veg values
            self.veg_type = topo.veg_type
            matching = [s for s in self.config.keys() if "winstral_veg_" in s]
            v = {}
            for m in matching:
                if m != 'winstral_veg_default':
                    ms = m.split('_')
                    # v[ms[1]] = float(self.config[m])
                    if type(self.config[m]) == list:
                        v[ms[1]] = float(self.config[m][0])
                    else:
                        v[ms[1]] = float(self.config[m])
            self.veg = v

    def distribute(self, data, dpt, precip_temp, ta, time, wind, temp,
                   wind_direction=None, dir_round_cell=None, wind_speed=None,
                   cell_maxus=None):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`.

        The following steps are taken when distributing precip, if there is
        precipitation measured:

        1. Distribute the instantaneous precipitation from the measurement data
        2. Determine the distributed precipitation phase based on the
            precipitation temperature
        3. Calculate the storms based on the accumulated mass, time since last
            storm, and precipitation phase threshold


        Args:
            data:           Pandas dataframe for a single time step from precip
            dpt:            dew point numpy array that will be used for
            precip_temp:    numpy array of the precipitation temperature
            ta:             air temp numpy array
            time:           pass in the time were are currently on
            wind:           station wind speed at time step
            temp:           station air temperature at time step
            wind_direction: numpy array for simulated wind direction
            dir_round_cell: numpy array for wind direction in discreet
                            increments for referencing maxus at a specific
                            direction
            wind_speed:     numpy array of wind speed
            cell_maxus:     numpy array for maxus at correct wind directions
        """

        self._logger.debug('%s Distributing all precip' % data.name)
        data = data[self.stations]

        if self.config['distribution'] != 'grid':
            if self.nasde_model == 'marks2017':
                # Adjust the precip for undercatchment
                if self.config['station_adjust_for_undercatch']:
                    self._logger.debug(
                        '%s Adjusting precip for undercatch...' % data.name)
                    self.corrected_precip.loc[time] = \
                        precip.adjust_for_undercatch(
                            self.corrected_precip.loc[time],
                        wind,
                        temp,
                        self.config,
                        self.metadata)

                # Use the clipped and corrected precip
                self.distribute_for_marks2017(
                    self.corrected_precip.loc[time],
                    precip_temp,
                    ta,
                    time)

            else:
                # Adjust the precip for undercatchment
                if self.config['station_adjust_for_undercatch']:
                    self._logger.debug(
                        '%s Adjusting precip for undercatch...' % data.name)
                    data = precip.adjust_for_undercatch(
                        data,
                        wind,
                        temp,
                        self.config,
                        self.metadata)

                    self.distribute_for_susong1999(
                        data, precip_temp, time)
        else:
            self.distribute_for_susong1999(data, precip_temp, time)

        # redistribute due to wind to account for driftin
        if self.config['precip_rescaling_model'] == 'winstral':
            self._logger.debug('%s Redistributing due to wind' % data.name)
            if np.any(dpt < 0.5):
                self.precip = precip.dist_precip_wind(
                    self.precip,
                    dpt,
                    wind_direction,
                    dir_round_cell,
                    wind_speed,
                    cell_maxus,
                    self.tbreak,
                    self.tbreak_direction,
                    self.veg_type,
                    self.veg,
                    self.config)

    def distribute_for_marks2017(self, data, precip_temp, ta, time):
        """
        Specialized distribute function for working with the new accumulated
        snow density model Marks2017 requires storm total and a corrected
        precipitation as to avoid precip between storms.
        """
        # self.corrected_precip # = data.mul(self.storm_correction)

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

            if time == storm_start:
                # Entered into a new storm period distribute the storm total
                self._logger.debug('{0} Entering storm #{1}'
                                   .format(data.name, self.storm_id+1))
                if precip_temp.min() < 2.0:
                    self._logger.debug('''Distributing Total Precip
                                        for Storm #{0}'''
                                       .format(self.storm_id+1))
                    self._distribute(storm[self.stations].astype(float),
                                     other_attribute='storm_total')
                    self.storm_total = utils.set_min_max(self.storm_total,
                                                         self.min,
                                                         self.max)

            if self.storming and precip_temp.min() < 2.0:
                self._logger.debug('''Calculating new snow density for
                                    storm #{0}'''.format(self.storm_id+1))
                # determine the precip phase and den
                snow_den, perc_snow = snow.calc_phase_and_density(
                    precip_temp,
                    self.precip,
                    nasde_model=self.nasde_model)

            else:
                snow_den = np.zeros(self.precip.shape)
                perc_snow = np.zeros(self.precip.shape)

            # calculate decimal days since last storm
            self.storm_days = storms.time_since_storm_pixel(
                self.precip,
                precip_temp,
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

    def distribute_for_susong1999(self, data, ppt_temp, time):
        """Susong 1999 estimates percent snow and snow density based on
        Susong et al, (1999) :cite:`Susong&al:1999`.

        Args:
            data (pd.DataFrame): Precipitation mass data
            ppt_temp (pd.DataFrame): Precipitation temperature data
            time : Unused
        """

        if data.sum() > 0:

            self._distribute(data)
            self.precip = utils.set_min_max(self.precip, self.min, self.max)

            # determine the precip phase and den
            snow_den, perc_snow = snow.calc_phase_and_density(
                ppt_temp,
                self.precip,
                nasde_model=self.nasde_model)

            # determine the time since last storm
            stormDays, stormPrecip = storms.time_since_storm(
                self.precip,
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

    def distribute_thread(self, smrf_queue, data_queue):
        """
        Distribute the data using threading and queue. All data is provided and
        ``distribute_thread`` will go through each time step and call
        :mod:`smrf.distribute.precip.ppt.distribute` then puts the distributed
        data into the queue for:

        * :py:attr:`percent_snow`

        * :py:attr:`snow_density`
        * :py:attr:`storm_days`

        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
        """
        self._logger.info("Distributing {}".format(self.variable))

        for date_time in self.date_time:

            ppt_data = data_queue['precip'].get(date_time)
            ta_data = data_queue['air_temp'].get(date_time)
            ws_data = data_queue['wind_speed'].get(date_time)

            dpt = smrf_queue['dew_point'].get(date_time)
            precip_temp = smrf_queue['precip_temp'].get(date_time)
            ta = smrf_queue['air_temp'].get(date_time)

            # variables for wind redistribution
            if self.config['precip_rescaling_model'] == 'winstral':
                wind_direction = smrf_queue['wind_direction'].get(date_time)
                flatwind = smrf_queue['flatwind'].get(date_time)
                dir_round_cell = smrf_queue['dir_round_cell'].get(date_time)
                cell_maxus = smrf_queue['cellmaxus'].get(date_time)

            else:
                wind_direction = None
                flatwind = None
                dir_round_cell = None
                cell_maxus = None

            self.distribute(
                ppt_data,
                dpt,
                precip_temp,
                ta,
                date_time,
                ws_data,
                ta_data,
                wind_direction,
                dir_round_cell,
                flatwind,
                cell_maxus)

            smrf_queue[self.variable].put([date_time, self.precip])
            smrf_queue['percent_snow'].put([date_time, self.percent_snow])
            smrf_queue['snow_density'].put([date_time, self.snow_density])
            smrf_queue['storm_days'].put([date_time, self.storm_days])
            smrf_queue['storm_total'].put([date_time, self.storm_total])

            if self.nasde_model == "marks2017":
                smrf_queue['storm_id'].put([date_time, self.storm_id])

    def post_processor(self, main_obj, threaded=False):

        pass
