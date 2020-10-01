"""
The module :mod:`~smrf.framework.model_framework` contains functions and
classes that act as a major wrapper to the underlying packages and modules
contained with SMRF. A class instance of
:class:`~smrf.framework.model_framework.SMRF` is initialized with a
configuration file indicating where data is located, what variables to
distribute and how, where to output the distributed data, or run as a threaded
application. See the help on the configuration file to learn more about how to
control the actions of :class:`~smrf.framework.model_framework.SMRF`.

Example:
    The following examples shows the most generic method of running SMRF. These
    commands will generate all the forcing data required to run iSnobal.  A
    complete example can be found in run_smrf.py

    >>> import smrf
    >>> s = smrf.framework.SMRF(configFile) # initialize SMRF
    >>> s.loadTopo() # load topo data
    >>> s.create_distribution() # initialize the distribution
    >>> s.initializeOutput() # initialize the outputs if desired
    >>> s.loadData() # load weather data  and station metadata
    >>> s.disttribute_data() # distribute

"""

import logging
import os
import sys
from datetime import datetime
from os.path import abspath, join
from threading import Thread

import numpy as np
import pandas as pd
import pytz
from inicheck.config import UserConfig
from inicheck.output import generate_config, print_config_report
from inicheck.tools import check_config, get_user_config
from topocalc.shade import shade

from smrf import distribute
from smrf.data import InputData, Topo
from smrf.envphys import sunang
from smrf.envphys.solar import model
from smrf.framework import art, logger
from smrf.output import output_hru, output_netcdf
from smrf.utils import queue
from smrf.utils.utils import backup_input, date_range, getqotw


class SMRF():
    """
    SMRF - Spatial Modeling for Resources Framework

    Args:
        configFile (str):  path to configuration file.

    Returns:
        SMRF class instance.

    Attributes:
        start_date: start_date read from configFile
        end_date: end_date read from configFile
        date_time: Numpy array of date_time objects between start_date and
            end_date
        config: Configuration file read in as dictionary
        distribute: Dictionary the contains all the desired variables to
            distribute and is initialized in
            :func:`~smrf.framework.model_framework.create_distribution`
    """

    # These are the modules that the user can modify and use different methods
    modules = ['air_temp',
               'albedo',
               'precip',
               'soil_temp',
               'solar',
               'cloud_factor',
               'thermal',
               'vapor_pressure',
               'wind']

    BASE_THREAD_VARIABLES = frozenset([
        'cosz', 'azimuth', 'illum_ang', 'output'
    ])

    def __init__(self, config, external_logger=None):
        """
        Initialize the model, read config file, start and end date, and logging
        """
        # read the config file and store
        if isinstance(config, str):
            if not os.path.isfile(config):
                raise Exception('Configuration file does not exist --> {}'
                                .format(config))
            self.configFile = config

            # Read in the original users config
            ucfg = get_user_config(config, modules='smrf')

        elif isinstance(config, UserConfig):
            ucfg = config
            self.configFile = config.filename

        else:
            raise Exception('Config passed to SMRF is neither file name nor '
                            ' UserConfig instance')
        # start logging
        if external_logger is None:
            self.smrf_logger = logger.SMRFLogger(ucfg.cfg['system'])
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = external_logger

        # add the title
        self.title(2)

        # Make the output directory if it do not exist
        out = ucfg.cfg['output']['out_location']
        os.makedirs(out, exist_ok=True)

        # Check the user config file for errors and report issues if any
        self._logger.info("Checking config file for issues...")
        warnings, errors = check_config(ucfg)
        print_config_report(warnings, errors, logger=self._logger)
        self.ucfg = ucfg
        self.config = self.ucfg.cfg

        # Exit SMRF if config file has errors
        if len(errors) > 0:
            self._logger.error("Errors in the config file. See configuration"
                               " status report above.")
            sys.exit()

        # Write the config file to the output dir
        full_config_out = abspath(join(out, 'config.ini'))

        self._logger.info("Writing config file with full options.")
        generate_config(self.ucfg, full_config_out)

        # Process the system variables
        for k, v in self.config['system'].items():
            setattr(self, k, v)

        self._setup_date_and_time()

        # need to align date time
        if 'date_method_start_decay' in self.config['albedo'].keys():
            self.config['albedo']['date_method_start_decay'] = \
                self.config['albedo']['date_method_start_decay'].replace(
                    tzinfo=self.time_zone)
            self.config['albedo']['date_method_end_decay'] = \
                self.config['albedo']['date_method_end_decay'].replace(
                    tzinfo=self.time_zone)

        # if a gridded dataset will be used
        self.gridded = False
        self.forecast_flag = False
        self.hrrr_data_timestep = False
        if 'gridded' in self.config:
            self.gridded = True
            if self.config['gridded']['data_type'] in ['hrrr_grib']:
                self.forecast_flag = \
                    self.config['gridded']['hrrr_forecast_flag']
                self.hrrr_data_timestep = \
                    self.config['gridded']['hrrr_load_method'] == 'timestep'

        now = datetime.now().astimezone(self.time_zone)
        if ((self.start_date > now and not self.gridded) or
                (self.end_date > now and not self.gridded)):
            raise ValueError("A date set in the future can only be used with"
                             " WRF generated data!")

        self.distribute = {}

        if self.config['system']['qotw']:
            self._logger.info(getqotw())

        # Initialize the distribute dict
        self._logger.info('Started SMRF --> %s' % now)
        self._logger.info('Model start --> %s' % self.start_date)
        self._logger.info('Model end --> %s' % self.end_date)
        self._logger.info('Number of time steps --> %i' % self.time_steps)

    def _setup_date_and_time(self):
        self.time_zone = pytz.timezone(self.config['time']['time_zone'])
        is_utz = self.time_zone == pytz.UTC

        # Get the time section utils
        self.start_date = pd.to_datetime(
            self.config['time']['start_date'], utc=is_utz
        )
        self.end_date = pd.to_datetime(
            self.config['time']['end_date'], utc=is_utz
        )

        if not is_utz:
            self.start_date = self.start_date.tz_localize(self.time_zone)
            self.end_date = self.end_date.tz_localize(self.time_zone)

        # Get the time steps correctly in the time zone
        self.date_time = date_range(
            self.start_date,
            self.end_date,
            self.config['time']['time_step'],
            self.time_zone
        )
        self.time_steps = len(self.date_time)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Provide some logging info about when SMRF was closed
        """

        self._logger.info('SMRF closed --> %s' % datetime.now())
        logging.shutdown()

    @property
    def possible_output_variables(self):
        # Collect the potential output variables
        variables = {}
        for variable, module in self.distribute.items():
            variables.update(module.output_variables)
        return variables

    def loadTopo(self):
        """
        Load the information from the configFile in the ['topo'] section. See
        :func:`smrf.data.loadTopo.Topo` for full description.
        """

        self.topo = Topo(self.config['topo'])

    def create_distribution(self):
        """
        This initializes the distirbution classes based on the configFile
        sections for each variable.
        :func:`~smrf.framework.model_framework.SMRF.create_distribution`
        will initialize the variables within the :func:`smrf.distribute`
        package and insert into a dictionary 'distribute' with variable names
        as the keys.

        Variables that are intialized are:
            * :func:`Air temperature <smrf.distribute.air_temp.ta>`
            * :func:`Vapor pressure <smrf.distribute.vapor_pressure.vp>`
            * :func:`Wind speed and direction <smrf.distribute.wind.wind>`
            * :func:`Precipitation <smrf.distribute.precipitation.ppt>`
            * :func:`Albedo <smrf.distribute.albedo.Albedo>`
            * :func:`Solar radiation <smrf.distribute.solar.Solar>`
            * :func:`Thermal radiation <smrf.distribute.thermal.th>`
            * :func:`Soil Temperature <smrf.distribute.soil_temp.ts>`
        """

        # 1. Air temperature
        self.distribute['air_temp'] = distribute.air_temp.ta(
            self.config['air_temp'])

        # 2. Vapor pressure
        self.distribute['vapor_pressure'] = distribute.vapor_pressure.vp(
            self.config['vapor_pressure'],
            self.config['precip']['precip_temp_method'])

        # 3. Wind
        self.distribute['wind'] = distribute.wind.Wind(self.config)

        # 4. Precipitation
        self.distribute['precipitation'] = distribute.precipitation.ppt(
            self.config['precip'],
            self.start_date,
            self.config['time']['time_step'])

        # 5. Albedo
        self.distribute['albedo'] = distribute.albedo.Albedo(
            self.config['albedo'])

        # 6. cloud_factor
        self.distribute['cloud_factor'] = distribute.cloud_factor.cf(
            self.config['cloud_factor'])

        # 7. Solar radiation
        self.distribute['solar'] = distribute.solar.Solar(
            self.config,
            self.topo)

        # 8. thermal radiation
        self.distribute['thermal'] = distribute.thermal.th(
            self.config['thermal'])

        # 9. soil temperature
        self.distribute['soil_temp'] = distribute.soil_temp.ts(
            self.config['soil_temp'])

    def loadData(self):
        """
        Load the measurement point data for distributing to the DEM,
        must be called after the distributions are initialized. Currently, data
        can be loaded from three different sources:

            * :func:`CSV files <smrf.data.loadData.wxdata>`
            * :func:`MySQL database <smrf.data.loadData.wxdata>`
            * :func:`Gridded data source (WRF) <smrf.data.loadGrid.grid>`

        After loading, :func:`~smrf.framework.mode_framework.SMRF.loadData`
        will call :func:`smrf.framework.model_framework.find_pixel_location`
        to determine the pixel locations of the point measurements and filter
        the data to the desired stations if CSV files are used.
        """

        self.data = InputData(
            self.config,
            self.start_date,
            self.end_date,
            self.topo)

        # Pre-filter the data to the desired stations in
        # each [variable] section
        self._logger.debug(
            'Filter data to those specified in each variable section')
        for variable, module in self.data.MODULE_VARIABLES.items():

            # Check to find the matching stations
            data = getattr(self.data, variable, pd.DataFrame())
            if self.distribute[module].stations is not None:

                match = data.columns.isin(self.distribute[module].stations)
                sta_match = data.columns[match]

                # Update the dataframe and the distribute stations
                self.distribute[module].stations = sta_match.tolist()
                setattr(self.data, variable, data[sta_match])

            else:
                self.distribute[module].stations = data.columns.tolist()

        # Does the user want to create a CSV copy of the station data used.
        if self.config["output"]['input_backup']:
            self._logger.info('Backing up input data...')
            backup_input(self.data, self.ucfg)

    def disttribute_data(self):
        """
        Wrapper for various distribute methods. If threading was set in
        configFile, then
        :func:`~smrf.framework.model_framework.SMRF.disttribute_data_threaded`
        will be called. Default will call
        :func:`~smrf.framework.model_framework.SMRF.disttribute_data_serial`.
        """

        if self.threading:
            self.disttribute_data_threaded()
        else:
            self.disttribute_data_serial()

    def initialize_distribution(self, date_time=None):
        """Call the initialize method for each distribute module

        Args:
            date_time (list, optional): initialize with the datetime list
                or not. Defaults to None.
        """

        for v in self.distribute:
            self.distribute[v].initialize(self.topo, self.data, date_time)

    def disttribute_data_serial(self):
        """
        Distribute the measurement point data for all variables in serial. Each
        variable is initialized first using the :func:`smrf.data.loadTopo.Topo`
        instance and the metadata loaded from
        :func:`~smrf.framework.model_framework.SMRF.loadData`.
        The function distributes over each time step, all the variables below.

        Steps performed:
            1. Sun angle for the time step
            2. Illumination angle
            3. Air temperature
            4. Vapor pressure
            5. Wind direction and speed
            6. Precipitation
            7. Cloud Factor
            8. Solar radiation
            9. Thermal radiation
            10. Soil temperature
            11. Output time step if needed
        """

        self.initialize_distribution()

        # -------------------------------------
        # Distribute the data
        for output_count, t in enumerate(self.date_time):

            startTime = datetime.now()

            self.distribute_single_timestep(t)
            self.output(t)

            telapsed = datetime.now() - startTime
            self._logger.debug('{0:.2f} seconds for time step'
                               .format(telapsed.total_seconds()))

        self.forcing_data = 1

    def distribute_single_timestep(self, t):

        self._logger.info('Distributing time step {}'.format(t))

        if self.hrrr_data_timestep:
            self.data.load_class.load_timestep(t)
            self.data.set_variables()

        # 0.1 sun angle for time step
        cosz, azimuth, rad_vec = sunang.sunang(
            t.astimezone(pytz.utc),
            self.topo.basin_lat,
            self.topo.basin_long)

        # 0.2 illumination angle
        illum_ang = None
        if cosz > 0:
            illum_ang = shade(
                self.topo.sin_slope,
                self.topo.aspect,
                azimuth,
                cosz)

        # 1. Air temperature
        self.distribute['air_temp'].distribute(self.data.air_temp.loc[t])

        # 2. Vapor pressure
        self.distribute['vapor_pressure'].distribute(
            self.data.vapor_pressure.loc[t],
            self.distribute['air_temp'].air_temp)

        # 3. Wind_speed and wind_direction
        self.distribute['wind'].distribute(
            self.data.wind_speed.loc[t],
            self.data.wind_direction.loc[t],
            t)

        # 4. Precipitation
        self.distribute['precipitation'].distribute(
            self.data.precip.loc[t],
            self.distribute['vapor_pressure'].dew_point,
            self.distribute['vapor_pressure'].precip_temp,
            self.distribute['air_temp'].air_temp,
            t,
            self.data.wind_speed.loc[t],
            self.data.air_temp.loc[t],
            self.distribute['wind'].wind_direction,
            self.distribute['wind'].wind_model.dir_round_cell,
            self.distribute['wind'].wind_speed,
            self.distribute['wind'].wind_model.cellmaxus)

        # 5. Albedo
        self.distribute['albedo'].distribute(
            t,
            illum_ang,
            self.distribute['precipitation'].storm_days)

        # 6. cloud_factor
        self.distribute['cloud_factor'].distribute(
            self.data.cloud_factor.loc[t])

        # 7. Solar
        self.distribute['solar'].distribute(
            t,
            self.distribute["cloud_factor"].cloud_factor,
            illum_ang,
            cosz,
            azimuth,
            self.distribute['albedo'].albedo_vis,
            self.distribute['albedo'].albedo_ir)

        # 8. thermal radiation
        self.distribute['thermal'].distribute(
            t,
            self.distribute['air_temp'].air_temp,
            self.distribute['vapor_pressure'].vapor_pressure,
            self.distribute['vapor_pressure'].dew_point,
            self.distribute['cloud_factor'].cloud_factor)

        # 9. Soil temperature
        self.distribute['soil_temp'].distribute()

    def disttribute_data_threaded(self):
        """
        Distribute the measurement point data for all variables using threading
        and queues. Each variable is initialized first using the
        :func:`smrf.data.loadTopo.Topo` instance and the metadata loaded from
        :func:`~smrf.framework.model_framework.SMRF.loadData`. A
        :func:`DateQueue <smrf.utils.queue.DateQueue_Threading>` is initialized
        for :attr:`all threading
        variables <smrf.framework.model_framework.SMRF.thread_variables>`. Each
        variable in :func:`smrf.distribute` is passed all the required point
        data at once using the distribute_thread function.  The
        distribute_thread function iterates over
        :attr:`~smrf.framework.model_framework.SMRF.date_time` and places the
        distributed values into the
        :func:`DateQueue <smrf.utils.queue.DateQueue_Threading>`.
        """

        # Load the data into the data queue
        self.create_data_queue()

        # Create threads for distribution
        self.create_distributed_threads()

        # output thread
        self.threads.append(
            queue.QueueOutput(
                self.smrf_queue,
                self.date_time,
                self.out_func,
                self.config['output']['frequency'],
                self.topo.nx,
                self.topo.ny))

        # the cleaner
        self.threads.append(queue.QueueCleaner(
            self.date_time, self.smrf_queue))

        # start all the threads
        for i in range(len(self.threads)):
            self.threads[i].start()

        # Wait for the end
        for i in range(len(self.threads)):
            self.threads[i].join()

        self._logger.debug('DONE!!!!')

    def create_data_queue(self):

        self._logger.info('Creating the data queue and loading current data')

        self.data_queue = {}
        for variable in self.data.VARIABLES[:-1]:
            dq = queue.DateQueueThreading(
                timeout=self.time_out,
                name="data_{}".format(variable))

            # load the data into the queue, all methods should have
            # loaded something, even the HRRR will have a single hour
            # of data loaded.
            data = getattr(self.data, variable, pd.DataFrame())
            for date_time, row in data.iterrows():
                dq.put([date_time, row])

            self.data_queue[variable] = dq

        # create a thread to load the data
        if self.hrrr_data_timestep:
            data_thread = Thread(
                target=self.data.load_class.load_timestep_thread,
                name='data',
                args=(self.date_time, self.data_queue))
            data_thread.start()

    def set_queue_variables(self):

        # These are the variables that will be queued
        self.thread_queue_variables = list(self.BASE_THREAD_VARIABLES)

        for v in self.distribute:
            self.thread_queue_variables += self.distribute[v].thread_variables

    def create_distributed_threads(self, other_queue=None):
        """
        Creates the threads for a distributed run in smrf.
        Designed for smrf runs in memory

        Returns
            t: list of threads for distirbution
            q: queue
        """

        # -------------------------------------
        # Initialize the distributions and get thread variables
        self._logger.info("Initializing distributed variables...")

        self.initialize_distribution(self.date_time)
        self.set_queue_variables()

        # -------------------------------------
        # Create Queues for all the variables
        self.smrf_queue = {}
        self._logger.info("Staging {} threaded variables...".format(
            len(self.thread_queue_variables)))
        for v in self.thread_queue_variables:
            self.smrf_queue[v] = queue.DateQueueThreading(
                self.queue_max_values,
                self.time_out,
                name=v)

        # -------------------------------------
        # Distribute the data
        self.threads = []

        # 0.1 sun angle for time step
        self.threads.append(Thread(
            target=sunang.sunang_thread,
            name='sun_angle',
            args=(self.smrf_queue, self.date_time,
                  self.topo.basin_lat,
                  self.topo.basin_long)))

        # 0.2 illumination angle
        self.threads.append(Thread(
            target=model.shade_thread,
            name='illum_angle',
            args=(self.smrf_queue, self.date_time,
                  self.topo.sin_slope, self.topo.aspect)))

        thread_dict = {
            'air_temp': self.distribute['air_temp'].distribute_thread,
            'vapor_pressure': self.distribute['vapor_pressure'].distribute_thread,  # noqa
            'wind': self.distribute['wind'].distribute_thread,
            'precipitation': self.distribute['precipitation'].distribute_thread,  # noqa
            'albedo': self.distribute['albedo'].distribute_thread,
            'cloud_factor': self.distribute['cloud_factor'].distribute_thread,
            'solar': self.distribute['solar'].distribute_thread,
            'thermal': self.distribute['thermal'].distribute_thread
        }

        for name, target in thread_dict.items():
            self.threads.append(
                Thread(
                    target=target,
                    name=name,
                    args=(self.smrf_queue, self.data_queue))
            )

    def create_output_variable_dict(self, output_variables, out_location):

        # determine which variables belong where
        variable_dict = {}
        for output_variable in output_variables:

            if output_variable in self.possible_output_variables.keys():
                fname = join(out_location, output_variable)
                module = self.possible_output_variables[output_variable]['module']  # noqa

                # TODO this is a hack to not have to redo the gold files
                if module == 'precipitation':
                    nc_module = 'precip'
                else:
                    nc_module = module

                variable_dict[output_variable] = {
                    'variable': output_variable,
                    'module': nc_module,
                    'out_location': fname,
                    'info': self.distribute[module].output_variables[output_variable]  # noqa
                }

            else:
                self._logger.error(
                    '{} not an output variable'.format(output_variable))

        return variable_dict

    def initializeOutput(self):
        """
        Initialize the output files based on the configFile section ['output'].
        Currently only :func:`NetCDF files
        <smrf.output.output_netcdf.OutputNetcdf>` are supported.
        """
        out_location = self.config['output']['out_location']

        # determine the variables to be output
        s_var_list = ", ".join(self.config['output']['variables'])
        self._logger.info('{} variables will be output'.format(s_var_list))

        output_variables = self.config['output']['variables']

        variable_dict = self.create_output_variable_dict(
            output_variables, out_location)

        self._logger.debug('{} of {} variables will be output'.format(
            len(output_variables), len(self.possible_output_variables)))

        # determine what type of file to output
        if self.config['output']['file_type'].lower() == 'netcdf':
            self.out_func = output_netcdf.OutputNetcdf(
                variable_dict, self.topo,
                self.config['time'],
                self.config['output'])

        elif self.config['output']['file_type'].lower() == 'hru':
            self.out_func = output_hru.output_hru(
                variable_dict, self.topo,
                self.date_time,
                self.config['output'])

        else:
            raise Exception('Could not determine type of file for output')

        # is there a function to apply?
        self.out_func.func = None
        if 'func' in self.config['output']:
            self.out_func.func = self.config['output']['func']

    def output(self, current_time_step,  module=None, out_var=None):
        """
        Output the forcing data or model outputs for the current_time_step.

        Args:
            current_time_step (date_time): the current time step datetime
                                            object

            module (str): module name
            out_var (str) - output a single variable

        """
        output_count = self.date_time.index(current_time_step)

        # Only output according to the user specified value,
        # or if it is the end.
        if (output_count % self.config['output']['frequency'] == 0) or \
           (output_count == len(self.date_time)):

            # User is attempting to output single variable
            if module is not None and out_var is not None:
                # add only one variable to the output list and preceed
                var_vals = [self.out_func.variable_dict[out_var]]

            # Incomplete request
            elif module is not None or out_var is not None:
                raise ValueError("Function requires an output module and"
                                 " variable name when outputting a specific"
                                 " variables")

            else:
                # Output all the variables
                var_vals = self.out_func.variable_dict.values()

            # Get the output variables then pass to the function
            for v in var_vals:
                # get the data desired
                data = getattr(
                    self.distribute[v['info']['module']], v['variable'])

                if data is None:
                    data = np.zeros((self.topo.ny, self.topo.nx))

                # output the time step
                self._logger.debug("Outputting {0}".format(v['module']))
                self.out_func.output(v['variable'], data, current_time_step)

    def post_process(self):
        """
        Execute all the post processors
        """

        for k in self.distribute.keys():
            self.distribute[k].post_processor(self)

    def title(self, option):
        """
        A little title to go at the top of the logger file
        """

        if option == 1:
            title = art.title1

        elif option == 2:
            title = art.title2

        for line in title:
            self._logger.info(line)


def run_smrf(config, external_logger=None):
    """
    Function that runs smrf how it should be operate for full runs.

    Args:
        config: string path to the config file or inicheck UserConfig instance
    """
    start = datetime.now()
    # initialize
    with SMRF(config, external_logger) as s:
        # load topo data
        s.loadTopo()

        # initialize the distribution
        s.create_distribution()

        # initialize the outputs if desired
        s.initializeOutput()

        # load weather data  and station metadata
        s.loadData()

        # distribute
        s.disttribute_data()

        # post process if necessary
        s.post_process()

        s._logger.info(datetime.now() - start)

    return s


def can_i_run_smrf(config):
    """
    Function that wraps run_smrf in try, except for testing purposes

    Args:
        config: string path to the config file or inicheck UserConfig instance
    """
    try:
        run_smrf(config)
        return True
    except Exception as e:
        raise e
        return False
