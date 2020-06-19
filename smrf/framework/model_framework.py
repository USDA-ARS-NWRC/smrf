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
    >>> s.initializeDistribution() # initialize the distribution
    >>> s.initializeOutput() # initialize the outputs if desired
    >>> s.loadData() # load weather data  and station metadata
    >>> s.distributeData() # distribute

"""

import logging
import os
import shutil
import sys
from datetime import datetime
from os.path import abspath, dirname, join
from threading import Thread

import coloredlogs
import numpy as np
import pandas as pd
import pytz
from inicheck.config import UserConfig
from inicheck.output import generate_config, print_config_report
from inicheck.tools import check_config, get_user_config
from topocalc.shade import shade

from smrf import data, distribute, output
from smrf.envphys import sunang
from smrf.envphys.solar import model
from smrf.utils import queue
from smrf.utils.utils import backup_input, check_station_colocation, getqotw


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
            :func:`~smrf.framework.model_framework.initializeDistribution`
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

    # These are the variables that will be queued
    thread_variables = ['cosz', 'azimuth', 'illum_ang',
                        'air_temp', 'dew_point', 'vapor_pressure',
                        'wind_speed', 'precip', 'percent_snow',
                        'snow_density', 'last_storm_day_basin',
                        'storm_days', 'precip_temp',
                        'clear_vis_beam', 'clear_vis_diffuse',
                        'clear_ir_beam', 'clear_ir_diffuse',
                        'albedo_vis', 'albedo_ir', 'net_solar',
                        'cloud_factor', 'thermal',
                        'output', 'veg_ir_beam', 'veg_ir_diffuse',
                        'veg_vis_beam', 'veg_vis_diffuse',
                        'cloud_ir_beam', 'cloud_ir_diffuse', 'cloud_vis_beam',
                        'cloud_vis_diffuse', 'thermal_clear', 'wind_direction']

    def __init__(self, config, external_logger=None):
        """
        Initialize the model, read config file, start and end date, and logging
        """
        # read the config file and store
        if isinstance(config, str):
            if not os.path.isfile(config):
                raise Exception('Configuration file does not exist --> {}'
                                .format(config))
            configFile = config

            # Read in the original users config
            ucfg = get_user_config(config, modules='smrf')

        elif isinstance(config, UserConfig):
            ucfg = config
            configFile = config.filename

        else:
            raise Exception('Config passed to SMRF is neither file name nor '
                            ' UserConfig instance')
        # start logging
        if external_logger is None:

            if 'log_level' in ucfg.cfg['system']:
                loglevel = ucfg.cfg['system']['log_level'].upper()
            else:
                loglevel = 'INFO'

            numeric_level = getattr(logging, loglevel, None)
            if not isinstance(numeric_level, int):
                raise ValueError('Invalid log level: %s' % loglevel)

            # setup the logging
            logfile = None
            if ucfg.cfg['system']['log_file'] is not None:
                logfile = ucfg.cfg['system']['log_file']
                if not os.path.isabs(logfile):
                    logfile = abspath(join(
                        dirname(configFile),
                        ucfg.cfg['system']['log_file']))

                if not os.path.isdir(dirname(logfile)):
                    os.makedirs(dirname(logfile))

                if not os.path.isfile(logfile):
                    with open(logfile, 'w+') as f:
                        f.close()

            fmt = '%(levelname)s:%(name)s:%(message)s'
            if logfile is not None:
                logging.basicConfig(filename=logfile,
                                    level=numeric_level,
                                    filemode='w+',
                                    format=fmt)
            else:
                logging.basicConfig(level=numeric_level)
                coloredlogs.install(level=numeric_level, fmt=fmt)

            self._loglevel = numeric_level

            self._logger = logging.getLogger(__name__)
        else:
            self._logger = external_logger

        # add the title
        title = self.title(2)
        for line in title:
            self._logger.info(line)

        out = ucfg.cfg['output']['out_location']

        # Make the tmp and output directories if they do not exist
        makeable_dirs = [out, join(out, 'tmp')]
        for path in makeable_dirs:
            if not os.path.isdir(path):
                try:
                    self._logger.info("Directory does not exist, Creating:\n{}"
                                      "".format(path))
                    os.makedirs(path)

                except OSError as e:
                    raise e

        self.temp_dir = path

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

        os.environ['WORKDIR'] = self.temp_dir

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
        if 'gridded' in self.config:
            self.gridded = True
            if self.config['gridded']['data_type'] in ['hrrr_netcdf', 'hrrr_grib']:  # noqa
                self.forecast_flag = self.config['gridded']['hrrr_forecast_flag']  # noqa

            # hours from start of day
            self.day_hour = self.start_date - self.date_time[0]
            self.day_hour = int(self.day_hour / np.timedelta64(1, 'h'))

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
        self.date_time = list(pd.date_range(
            self.start_date,
            self.end_date,
            freq="{[time][time_step]}min".format(self.config),
            tz=self.time_zone
        ))
        self.time_steps = len(self.date_time)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Provide some logging info about when SMRF was closed
        """

        if hasattr(self, 'temp_dir'):
            if os.path.isdir(self.temp_dir):
                shutil.rmtree(self.temp_dir)

        self._logger.info('SMRF closed --> %s' % datetime.now())

    def loadTopo(self):
        """
        Load the information from the configFile in the ['topo'] section. See
        :func:`smrf.data.loadTopo.Topo` for full description.
        """

        # load the topo
        self.topo = data.loadTopo.Topo(
            self.config['topo'],
            tempDir=self.temp_dir)

    def initializeDistribution(self):
        """
        This initializes the distirbution classes based on the configFile
        sections for each variable.
        :func:`~smrf.framework.model_framework.SMRF.initializeDistribution`
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
        self.distribute['precip'] = distribute.precipitation.ppt(
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

        # get the start date and end date requested

        flag = True
        if 'csv' in self.config:
            self.data = data.loadData.wxdata(
                self.config['csv'],
                self.start_date,
                self.end_date,
                time_zone=self.time_zone,
                dataType='csv')

        elif 'mysql' in self.config:
            self.data = data.loadData.wxdata(
                self.config['mysql'],
                self.start_date,
                self.end_date,
                time_zone=self.time_zone,
                dataType='mysql')

        elif 'gridded' in self.config:
            flag = False
            self.data = data.loadGrid.grid(
                self.config['gridded'],
                self.topo,
                self.start_date,
                self.end_date,
                time_zone=self.time_zone,
                dataType=self.config['gridded']['data_type'],
                tempDir=self.temp_dir,
                forecast_flag=self.forecast_flag,
                day_hour=self.day_hour)

            # set the stations in the distribute
            try:
                for key in self.distribute.keys():
                    setattr(self.distribute[key],
                            'stations',
                            self.data.metadata.index.tolist())

            except Exception as e:
                self._logger.warning("Distribution not initialized, grid"
                                     " stations could not be set.")
                self._logger.exception(e)

        else:
            raise KeyError('Could not determine where station data is located')

        # determine the locations of the stations on the grid while
        # maintaining reverse compatibility
        # New DB uses utm_x utm_y instead of X,Y
        try:
            self.data.metadata['xi'] = self.data.metadata.apply(
                lambda row: find_pixel_location(
                    row,
                    self.topo.x,
                    'utm_x'), axis=1)
            self.data.metadata['yi'] = self.data.metadata.apply(
                lambda row: find_pixel_location(
                    row,
                    self.topo.y,
                    'utm_y'), axis=1)
        # Old DB has X and Y
        except:

            self.data.metadata['xi'] = self.data.metadata.apply(
                lambda row: find_pixel_location(
                    row,
                    self.topo.x,
                    'X'), axis=1)
            self.data.metadata['yi'] = self.data.metadata.apply(
                lambda row: find_pixel_location(
                    row,
                    self.topo.y,
                    'Y'), axis=1)

        # Pre-filter the data to only the desired stations
        if flag:
            for key in self.distribute.keys():
                if key in self.data.variables:
                    # Pull out the loaded data
                    d = getattr(self.data, key)

                    # Check to find the matching stations
                    if self.distribute[key].stations is not None:

                        match = d.columns.isin(self.distribute[key].stations)
                        sta_match = d.columns[match]

                        # Update the dataframe and the distribute stations
                        self.distribute[key].stations = sta_match.tolist()
                        setattr(self.data, key, d[sta_match])
                    else:
                        self._logger.warning("Distribution not initialized,"
                                             " data not filtered to desired"
                                             " stations in variable {}"
                                             "".format(key))

            # Check all sections for stations that are colocated
            for key in self.distribute.keys():
                if key in self.data.variables:
                    if self.distribute[key].stations is not None:
                        # Confirm out stations all have a unique position
                        colocated = check_station_colocation(
                            metadata=self.data.metadata.loc[self.distribute[key].stations])

                        # Stations are co-located, throw error
                        if colocated is not None:
                            self._logger.error(
                                "Stations in the {0} section "
                                "are colocated.\n{1}".format(
                                    key, ','.join(colocated[0])))
                            sys.exit()

        # clip the timeseries to the start and end date
        for key in self.data.variables:
            if hasattr(self.data, key):
                d = getattr(self.data, key)
                d = d[self.start_date:self.end_date]
                setattr(self.data, key, d)

        # Does the user want to create a CSV copy of the station data used.
        if self.config["output"]['input_backup']:
            self._logger.info('Backing up input data...')
            backup_input(self.data, self.ucfg)

    def distributeData(self):
        """
        Wrapper for various distribute methods. If threading was set in
        configFile, then
        :func:`~smrf.framework.model_framework.SMRF.distributeData_threaded`
        will be called. Default will call
        :func:`~smrf.framework.model_framework.SMRF.distributeData_single`.
        """

        if self.threading:
            self.distributeData_threaded()
        else:
            self.distributeData_single()

    def distributeData_single(self):
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

        # -------------------------------------
        # Initialize the distibution
        for v in self.distribute:
            self.distribute[v].initialize(self.topo, self.data)

        # -------------------------------------
        # Distribute the data
        for output_count, t in enumerate(self.date_time):
            # wait here for the model to catch up if needed

            startTime = datetime.now()

            self._logger.info('Distributing time step %s' % t)
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
            self.distribute['precip'].distribute(
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
                self.distribute['precip'].storm_days)

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

            # 7. thermal radiation
            if self.distribute['thermal'].gridded and \
               self.config['gridded']['data_type'] in ['wrf', 'netcdf']:
                self.distribute['thermal'].distribute_thermal(
                    self.data.thermal.loc[t],
                    self.distribute['air_temp'].air_temp)
            else:
                self.distribute['thermal'].distribute(
                    t,
                    self.distribute['air_temp'].air_temp,
                    self.distribute['vapor_pressure'].vapor_pressure,
                    self.distribute['vapor_pressure'].dew_point,
                    self.distribute['cloud_factor'].cloud_factor)

            # 8. Soil temperature
            self.distribute['soil_temp'].distribute()

            # 9. output at the frequency and the last time step
            self.output(t)

            telapsed = datetime.now() - startTime
            self._logger.debug('{0:.2f} seconds for time step'
                               .format(telapsed.total_seconds()))

        self.forcing_data = 1

    def distributeData_threaded(self):
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
        # Create threads for distribution
        t, q = self.create_distributed_threads()

        # output thread
        t.append(queue.QueueOutput(q, self.date_time,
                                   self.out_func,
                                   self.config['output']['frequency'],
                                   self.topo.nx,
                                   self.topo.ny))

        # the cleaner
        t.append(queue.QueueCleaner(self.date_time, q))

        # start all the threads
        for i in range(len(t)):
            t[i].start()

        # Wait for the end
        for i in range(len(t)):
            t[i].join()

        self._logger.debug('DONE!!!!')

    def create_distributed_threads(self):
        """
        Creates the threads for a distributed run in smrf.
        Designed for smrf runs in memory

        Returns
            t: list of threads for distirbution
            q: queue
        """

        # -------------------------------------
        # Initialize the distibutions
        self._logger.info("Initializing distributed variables...")

        for v in self.distribute:
            self.distribute[v].initialize(self.topo, self.data)

        # -------------------------------------
        # Create Queues for all the variables
        q = {}
        t = []

        # Add threaded variables on the fly
        self.thread_variables += ['storm_total']
        self.thread_variables += ['flatwind']
        self.thread_variables += ['cellmaxus', 'dir_round_cell']

        if self.distribute['precip'].nasde_model == 'marks2017':
            self.thread_variables += ['storm_id']

        if self.distribute['thermal'].correct_cloud:
            self.thread_variables += ['thermal_cloud']

        if self.distribute['thermal'].correct_veg:
            self.thread_variables += ['thermal_veg']

        self._logger.info("Staging {} threaded variables...".format(
            len(self.thread_variables)))
        for v in self.thread_variables:
            q[v] = queue.DateQueue_Threading(self.queue_max_values,
                                             self.time_out,
                                             name=v)

        # -------------------------------------
        # Distribute the data

        # 0.1 sun angle for time step
        t.append(Thread(
            target=sunang.sunang_thread,
            name='sun_angle',
            args=(q, self.date_time,
                  self.topo.basin_lat,
                  self.topo.basin_long)))

        # 0.2 illumination angle
        t.append(Thread(
            target=model.shade_thread,
            name='illum_angle',
            args=(q, self.date_time,
                  self.topo.sin_slope, self.topo.aspect)))

        # 1. Air temperature
        t.append(Thread(
            target=self.distribute['air_temp'].distribute_thread,
            name='air_temp',
            args=(q, self.data.air_temp)))

        # 2. Vapor pressure
        t.append(Thread(
            target=self.distribute['vapor_pressure'].distribute_thread,
            name='vapor_pressure',
            args=(q, self.data.vapor_pressure)))

        # 3. Wind_speed and wind_direction
        t.append(Thread(
            target=self.distribute['wind'].distribute_thread,
            name='wind',
            args=(q, self.data.wind_speed,
                  self.data.wind_direction)))

        # 4. Precipitation
        t.append(Thread(
            target=self.distribute['precip'].distribute_thread,
            name='precipitation',
            args=(q, self.data, self.date_time,
                  self.topo.mask)))

        # 5. Albedo
        t.append(Thread(
            target=self.distribute['albedo'].distribute_thread,
            name='albedo',
            args=(q, self.date_time)))

        # 6.Cloud Factor
        t.append(Thread(
            target=self.distribute['cloud_factor'].distribute_thread,
            name='cloud_factor',
            args=(q, self.data.cloud_factor)))

        # 7 Net radiation
        t.append(Thread(
            target=self.distribute['solar'].distribute_thread,
            name='solar',
            args=(q, self.data.cloud_factor)))

        # 8. thermal radiation
        if self.distribute['thermal'].gridded:
            t.append(Thread(
                target=self.distribute['thermal'].distribute_thermal_thread,
                name='thermal',
                args=(q, self.data.thermal)))
        else:
            t.append(Thread(
                target=self.distribute['thermal'].distribute_thread,
                name='thermal',
                args=(q, self.date_time)))

        return t, q

    def initializeOutput(self):
        """
        Initialize the output files based on the configFile section ['output'].
        Currently only :func:`NetCDF files <smrf.output.output_netcdf.OutputNetcdf>` is
        supported.
        """
        out = self.config['output']['out_location']

        if self.config['output']['frequency'] is not None:

            # determine the variables to be output
            s_var_list = ", ".join(self.config['output']['variables'])
            self._logger.info('{} variables will be output'.format(s_var_list))

            output_variables = self.config['output']['variables']

            # determine which variables belong where
            variable_dict = {}
            for v in output_variables:
                for m in self.modules:

                    if m in self.distribute.keys():

                        if v in self.distribute[m].output_variables.keys():

                            # if there is a key in the config files output sec,
                            # then change the output file name
                            if v in self.config['output'].keys():
                                fname = join(out, self.config['output'][v])
                            else:
                                fname = join(out, v)

                            d = {
                                'variable': v,
                                'module': m,
                                'out_location': fname,
                                'info': self.distribute[m].output_variables[v]
                            }
                            variable_dict[v] = d

            # determine what type of file to output
            if self.config['output']['file_type'].lower() == 'netcdf':
                self.out_func = output.output_netcdf.OutputNetcdf(
                    variable_dict, self.topo,
                    self.config['time'],
                    self.config['output'])

            elif self.config['output']['file_type'].lower() == 'hru':
                self.out_func = output.output_hru.output_hru(
                    variable_dict, self.topo,
                    self.date_time,
                    self.config['output'])

            else:
                raise Exception('Could not determine type of file for output')

            # is there a function to apply?
            self.out_func.func = None
            if 'func' in self.config['output']:
                self.out_func.func = self.config['output']['func']

        else:
            self._logger.info('No variables will be output')
            self.output_variables = None

    def output(self, current_time_step,  module=None, out_var=None):
        """
        Output the forcing data or model outputs for the current_time_step.

        Args:
            current_time_step (date_time): the current time step datetime 
                                            object

            module -
            var_name -

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
                data = getattr(self.distribute[v['module']], v['variable'])

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
            title = ["  .----------------.  .----------------.  .----------------.  .----------------.",
                     " | .--------------. || .--------------. || .--------------. || .--------------. |",
                     " | |    _______   | || | ____    ____ | || |  _______     | || |  _________   | |",
                     " | |   /  ___  |  | || ||_   \  /   _|| || | |_   __ \    | || | |_   ___  |  | |",
                     " | |  |  (__ \_|  | || |  |   \/   |  | || |   | |__) |   | || |   | |_  \_|  | |",
                     " | |   '.___`-.   | || |  | |\  /| |  | || |   |  __ /    | || |   |  _|      | |",
                     " | |  |`\____) |  | || | _| |_\/_| |_ | || |  _| |  \ \_  | || |  _| |_       | |",
                     " | |  |_______.'  | || ||_____||_____|| || | |____| |___| | || | |_____|      | |",
                     " | |              | || |              | || |              | || |              | |",
                     " | '--------------' || '--------------' || '--------------' || '--------------' |",
                     "  '----------------'  '----------------'  '----------------'  '----------------' ",
                     " "]

        elif option == 2:
            title = ["    SSSSSSSSSSSSSSS  MMMMMMMM               MMMMMMMM RRRRRRRRRRRRRRRRR    FFFFFFFFFFFFFFFFFFFFFF",
                     "  SS:::::::::::::::S M:::::::M             M:::::::M R::::::::::::::::R   F::::::::::::::::::::F",
                     " S:::::SSSSSS::::::S M::::::::M           M::::::::M R::::::RRRRRR:::::R  F::::::::::::::::::::F",
                     " S:::::S     SSSSSSS M:::::::::M         M:::::::::M RR:::::R     R:::::R FF::::::FFFFFFFFF::::F",
                     " S:::::S             M::::::::::M       M::::::::::M   R::::R     R:::::R   F:::::F       FFFFFF",
                     " S:::::S             M:::::::::::M     M:::::::::::M   R::::R     R:::::R   F:::::F",
                     "  S::::SSSS          M:::::::M::::M   M::::M:::::::M   R::::RRRRRR:::::R    F::::::FFFFFFFFFF",
                     "   SS::::::SSSSS     M::::::M M::::M M::::M M::::::M   R:::::::::::::RR     F:::::::::::::::F",
                     "     SSS::::::::SS   M::::::M  M::::M::::M  M::::::M   R::::RRRRRR:::::R    F:::::::::::::::F",
                     "        SSSSSS::::S  M::::::M   M:::::::M   M::::::M   R::::R     R:::::R   F::::::FFFFFFFFFF",
                     "             S:::::S M::::::M    M:::::M    M::::::M   R::::R     R:::::R   F:::::F",
                     "             S:::::S M::::::M     MMMMM     M::::::M   R::::R     R:::::R   F:::::F",
                     " SSSSSSS     S:::::S M::::::M               M::::::M RR:::::R     R:::::R FF:::::::FF",
                     " S::::::SSSSSS:::::S M::::::M               M::::::M R::::::R     R:::::R F::::::::FF",
                     " S:::::::::::::::SS  M::::::M               M::::::M R::::::R     R:::::R F::::::::FF",
                     "  SSSSSSSSSSSSSSS    MMMMMMMM               MMMMMMMM RRRRRRRR     RRRRRRR FFFFFFFFFFF",
                     " "]

        return title


def run_smrf(config):
    """
    Function that runs smrf how it should be operate for full runs.

    Args:
        config: string path to the config file or inicheck UserConfig instance
    """
    start = datetime.now()
    # initialize
    with SMRF(config) as s:
        # load topo data
        s.loadTopo()

        # initialize the distribution
        s.initializeDistribution()

        # initialize the outputs if desired
        s.initializeOutput()

        # load weather data  and station metadata
        s.loadData()

        # distribute
        s.distributeData()

        # post process if necessary
        s.post_process()

        s._logger.info(datetime.now() - start)


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


def find_pixel_location(row, vec, a):
    """
    Find the index of the stations X/Y location in the model domain

    Args:
        row (pandas.DataFrame): metadata rows
        vec (nparray): Array of X or Y locations in domain
        a (str): Column in DataFrame to pull data from (i.e. 'X')

    Returns:
        Pixel value in vec where row[a] is located
    """
    return np.argmin(np.abs(vec - row[a]))
