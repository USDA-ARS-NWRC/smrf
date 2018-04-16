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
import sys
import coloredlogs
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pytz

from smrf import data, distribute, output, __core_config__
from smrf.envphys import radiation
from smrf.utils import queue, io
from smrf.utils.utils import backup_input, getqotw, check_station_colocation
from threading import Thread
import shutil

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
            :func:`~smrf.framework.model_framework.initializeDistirbution`
    """

    # These are the modules that the user can modify and use different methods
    modules = ['air_temp',
               'albedo',
               'precip',
               'soil_temp',
               'solar',
               'thermal',
               'vapor_pressure',
               'wind']

    # These are the variables that will be queued
    thread_variables = ['cosz', 'azimuth', 'illum_ang',
                        'air_temp', 'dew_point', 'vapor_pressure',
                        'wind_speed', 'precip', 'percent_snow',
                        'snow_density', 'last_storm_day_basin',
                        'storm_days',
                        'clear_vis_beam', 'clear_vis_diffuse',
                        'clear_ir_beam', 'clear_ir_diffuse',
                        'albedo_vis', 'albedo_ir', 'net_solar',
                        'cloud_factor', 'thermal',
                        'output', 'veg_ir_beam','veg_ir_diffuse',
                        'veg_vis_beam', 'veg_vis_diffuse',
                        'cloud_ir_beam', 'cloud_ir_diffuse', 'cloud_vis_beam',
                        'cloud_vis_diffuse', 'thermal_clear', 'wind_direction',
                        'flatwind', 'wind_direction', 'cellmaxus', 'dir_round_cell']

    def __init__(self, configFile, external_logger=None):
        """
        Initialize the model, read config file, start and end date, and logging
        """
        # read the config file and store
        if not os.path.isfile(configFile):
            raise Exception('Configuration file does not exist --> {}'
                            .format(configFile))

        try:
            #Read in the original users config
            self.config = io.get_user_config(configFile)

        except UnicodeDecodeError:
            raise Exception(('The configuration file is not encoded in '
                                    'UTF-8, please change and retry'))

        # start logging
        if external_logger == None:

            if 'log_level' in self.config['logging']:
                loglevel = self.config['logging']['log_level'].upper()
            else:
                loglevel = 'INFO'

            numeric_level = getattr(logging, loglevel, None)
            if not isinstance(numeric_level, int):
                raise ValueError('Invalid log level: %s' % loglevel)

            # setup the logging
            logfile = None
            if 'log_file' in self.config['logging']:
                logfile = self.config['logging']['log_file']
                if not os.path.isabs(logfile):
                    logfile = os.path.abspath(os.path.join(
                                            os.path.dirname(configFile),
                                            self.config['logging']['log_file']))

                if not os.path.isdir(os.path.dirname(logfile)):
                    os.makedirs(os.path.dirname(logfile))

                if not os.path.isfile(logfile):
                    with open(logfile,'w+') as f:
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

        #Make the tmp and output directories if they do not exist
        makeable_dirs = [self.config['output']['out_location'],os.path.join(self.config['output']['out_location'],'tmp')]
        for d in makeable_dirs:
            path = os.path.abspath(os.path.join(os.path.dirname(configFile),d))

            if not os.path.isdir(path):
                try:
                    #self._logger.info("Directory does not exist, \nCreating {0}".format(path))
                    os.makedirs(path)

                except OSError as e:
                    raise e

        self.temp_dir = path

        #Bring the the master config file
        mconfig = io.get_master_config()

        #Add defaults.
        self._logger.info("Adding defaults to config...")
        self.config = io.add_defaults(self.config, mconfig)

        #Check the user config file for errors and report issues if any
        self._logger.info("Checking config file for issues...")
        warnings, errors = io.check_config_file(self.config,mconfig,user_cfg_path=configFile)
        io.print_config_report(warnings, errors, logger = self._logger)

        #Exit SMRF if config file has errors
        if len(errors) > 0:
            self._logger.error("Errors in the config file. See configuration status report above.")
            sys.exit()

        #write the config file to the output dir no matter where the project was ran
        fname = 'config.ini'
        full_config_out = self.config['output']['out_location']
        full_config_out = os.path.abspath(os.path.join(os.path.dirname(configFile),full_config_out,fname))
        self._logger.info("Writing config file with full options.")
        io.generate_config(self.config,full_config_out)

        #After writing update the paths to be full abs paths.
        self.config = io.update_config_paths(self.config, configFile)

        # process the system variables
        for k,v in self.config['system'].items():
            setattr(self,k,v)

        os.environ['WORKDIR'] = self.temp_dir

        # get the time sectionutils
        self.start_date = pd.to_datetime(self.config['time']['start_date'])
        self.end_date = pd.to_datetime(self.config['time']['end_date'])

        #Check to see if user specified a real end time.
        if self.start_date > self.end_date:
            raise ValueError("start_date cannot be larger than end_date.")

        if self.start_date > datetime.now() and not self.gridded or self.end_date > datetime.now() and not self.gridded:
            raise ValueError("A date set in the future can only be used with WRF generated data!")

        #Get the timesetps correctly in the time zone
        d = data.mysql_data.date_range(self.start_date, self.end_date,
                                       timedelta(minutes=int(self.config['time']['time_step'])))
        tzinfo = pytz.timezone(self.config['time']['time_zone'])
        self.date_time = [di.replace(tzinfo=tzinfo) for di in d]
        self.time_steps = len(self.date_time)

        # if a gridded dataset will be used
        self.gridded = False
        if 'gridded' in self.config:
            self.gridded = True
            self.forecast_flag = self.config['gridded']['forecast_flag']
            self.n_forecast_hours = self.config['gridded']['n_forecast_hours']
            # hours from start of day
            self.day_hour = self.start_date - pd.to_datetime(d[0].strftime("%Y%m%d"))
            self.day_hour = int(self.day_hour / np.timedelta64(1, 'h'))


        self.distribute = {}

        if self.config['logging']['qotw']:
            self._logger.info(getqotw())

        # initialize the distribute dict
        self._logger.info('Started SMRF --> %s' % datetime.now())
        self._logger.info('Model start --> %s' % self.start_date)
        self._logger.info('Model end --> %s' % self.end_date)
        self._logger.info('Number of time steps --> %i' % self.time_steps)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Provide some logging info about when SMRF was closed
        """

        # clean up the WORKDIR
        if hasattr(self, 'topo'):
            if self.topo.stoporad_in_file is not None:
                if os.path.isfile(self.topo.stoporad_in_file):
                    os.remove(self.topo.stoporad_in_file)
        if hasattr(self, 'distribute'):
            if 'solar' in self.distribute.keys():
                if os.path.isfile(self.distribute['solar'].vis_file):
                    os.remove(self.distribute['solar'].vis_file)
                if os.path.isfile(self.distribute['solar'].ir_file):
                    os.remove(self.distribute['solar'].ir_file)

        if hasattr(self,'temp_dir'):
            if os.path.isdir(self.temp_dir):
                shutil.rmtree(self.temp_dir)

        self._logger.info('SMRF closed --> %s' % datetime.now())

    def loadTopo(self, calcInput=True):
        """
        Load the information from the configFile in the ['topo'] section. See
        :func:`smrf.data.loadTopo.topo` for full description.
        """

        # load the topo
        self.topo = data.loadTopo.topo(self.config['topo'],
                                       calcInput,
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
            * :func:`Albedo <smrf.distribute.albedo.albedo>`
            * :func:`Solar radiation <smrf.distribute.solar.solar>`
            * :func:`Thermal radiation <smrf.distribute.thermal.th>`
            * :func:`Soil Temperature <smrf.distribute.soil_temp.ts>`
        """

        # 1. Air temperature
        self.distribute['air_temp'] = \
            distribute.air_temp.ta(self.config['air_temp'])

        # 2. Vapor pressure
        self.distribute['vapor_pressure'] = \
            distribute.vapor_pressure.vp(self.config['vapor_pressure'])

        # 3. Wind
        self.distribute['wind'] = \
            distribute.wind.wind(self.config['wind'],
                                 self.temp_dir)

        # 4. Precipitation
        self.distribute['precip'] = \
            distribute.precipitation.ppt(self.config['precip'],
                                         self.start_date,
                                         self.config['time']['time_step'])

        # 5. Albedo
        self.distribute['albedo'] = \
            distribute.albedo.albedo(self.config['albedo'])

        # 6. Solar radiation
        self.distribute['solar'] = \
            distribute.solar.solar(self.config['solar'],
                                   self.distribute['albedo'].config,
                                   self.topo.stoporad_in_file,
                                   self.temp_dir)

        # 7. thermal radiation
        self.distribute['thermal'] = \
            distribute.thermal.th(self.config['thermal'])

        # 8. soil temperature
        self.distribute['soil_temp'] = \
            distribute.soil_temp.ts(self.config['soil_temp'])

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
            self.data = data.loadData.wxdata(self.config['csv'],
                                     self.start_date,
                                     self.end_date,
                                     time_zone=self.config['time']['time_zone'],
                                     stations=self.config['stations'],
                                     dataType='csv')

        elif 'mysql' in self.config:
            self.data = data.loadData.wxdata(self.config['mysql'],
                                     self.start_date,
                                     self.end_date,
                                     time_zone=self.config['time']['time_zone'],
                                     stations=self.config['stations'],
                                     dataType='mysql')

            #Add stations to stations in config for input backup
            self.config['stations']['stations'] = \
                                               self.data.metadata.index.tolist()

        elif 'gridded' in self.config:
            flag = False
            self.data = data.loadGrid.grid(self.config['gridded'],
                                   self.topo,
                                   self.start_date,
                                   self.end_date,
                                   time_zone=self.config['time']['time_zone'],
                                   dataType=self.config['gridded']['data_type'],
                                   tempDir=self.temp_dir,
                                   forecast_flag=self.forecast_flag,
                                   day_hour=self.day_hour,
                                   n_forecast_hours=self.n_forecast_hours)

            # set the stations in the distribute
            try:
                for key in self.distribute.keys():
                    setattr(self.distribute[key],
                            'stations',
                            self.data.metadata.index.tolist())
            except:
                self._logger.warning("Distribution not initialized, grid stations"
                                  "could not be set.")

        else:
            raise KeyError('Could not determine where station data is located')

        # determine the locations of the stations on the grid while maintaining reverse compatibility
        #New DB uses utm_x utm_y instead of X,Y
        try:
            self.data.metadata['xi'] = \
                self.data.metadata.apply(lambda row: find_pixel_location(row,
                                                                     self.topo.x,
                                                                     'utm_x'), axis=1)
            self.data.metadata['yi'] = \
                self.data.metadata.apply(lambda row: find_pixel_location(row,
                                                                     self.topo.y,
                                                                     'utm_y'), axis=1)
        #Old DB has X and Y
        except:
            self.data.metadata['xi'] = \
                self.data.metadata.apply(lambda row: find_pixel_location(row,
                                                                     self.topo.x,
                                                                     'X'), axis=1)
            self.data.metadata['yi'] = \
                self.data.metadata.apply(lambda row: find_pixel_location(row,
                                                                     self.topo.y,
                                                                                 'Y'), axis=1)

        # pre filter the data to only the desired stations
        if flag:
            try:
                for key in self.distribute.keys():
                    if key in self.data.variables:
                        # pull out the loaded data
                        d = getattr(self.data, key)

                        # check to find the matching stations
                        match = d.columns.isin(self.distribute[key].stations)
                        sta_match = d.columns[match]

                        # update the dataframe and the distribute stations
                        self.distribute[key].stations = sta_match.tolist()
                        setattr(self.data, key, d[sta_match])


                if hasattr(self.data, 'cloud_factor'):
                    d = getattr(self.data, 'cloud_factor')
                    setattr(self.data,
                            'cloud_factor',
                            d[self.distribute['solar'].stations])

            except Exception as e:
               self._logger.warning("Distribution not initialized, data not "
                                   "filtered to desired stations")
               self._logger.error(e)


            #Check all section for stations that are colocated
            for key in self.distribute.keys():
                if key in self.data.variables:
                    if self.distribute[key].stations != None:
                        #Confirm out stations all have a unique position for each section
                        colocated = check_station_colocation(metadata=self.data.metadata.loc[self.distribute[key].stations])

                        #Stations are co-located, throw error
                        if colocated != None:
                            self._logger.error("ERROR: Stations in the {0} section are colocated.\n{1}".format(key,','.join(colocated[0])))
                            sys.exit()

        #Does the user want to create a CSV copy of the station data used.
        if self.config["output"]['input_backup'] == True:
            self._logger.info('Backing up input data...')
            backup_input(self.data, self.config)

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
        variable is initialized first using the :func:`smrf.data.loadTopo.topo`
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
            7. Solar radiation
            8. Thermal radiation
            9. Soil temperature
            10. Output time step if needed
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
            cosz, azimuth = radiation.sunang(t.astimezone(pytz.utc),
                                             self.topo.topoConfig['basin_lat'],
                                             self.topo.topoConfig['basin_lon'],
                                             zone=0,
                                             slope=0,
                                             aspect=0)

            # 0.2 illumination angle
            illum_ang = None
            if cosz > 0:
                illum_ang = radiation.shade(self.topo.slope,
                                            self.topo.aspect,
                                            azimuth,
                                            cosz)

            # 1. Air temperature
            self.distribute['air_temp'].distribute(self.data.air_temp.loc[t])

            # 2. Vapor pressure
            self.distribute['vapor_pressure'].distribute(self.data.vapor_pressure.loc[t],
                                                        self.distribute['air_temp'].air_temp)

            # 3. Wind_speed and wind_direction
            self.distribute['wind'].distribute(self.data.wind_speed.loc[t],
                                               self.data.wind_direction.loc[t])
#self, data, dpt, time, wind, temp, mask=None
            # 4. Precipitation
            self.distribute['precip'].distribute(self.data.precip.loc[t],
                                                self.distribute['vapor_pressure'].dew_point,
                                                t,
                                                self.data.wind_speed.loc[t],
                                                self.data.air_temp.loc[t],
                                                self.distribute['wind'].wind_direction,
                                                self.distribute['wind'].dir_round_cell,
                                                self.distribute['wind'].wind_speed,
                                                self.distribute['wind'].cellmaxus
                                                self.topo.mask)

            # 5. Albedo
            self.distribute['albedo'].distribute(t,
                                                 illum_ang,
                                                 self.distribute['precip'].storm_days)

            # 6. Solar
            self.distribute['solar'].distribute(self.data.cloud_factor.loc[t],
                                                illum_ang,
                                                cosz,
                                                azimuth,
                                                self.distribute['precip'].last_storm_day_basin,
                                                self.distribute['albedo'].albedo_vis,
                                                self.distribute['albedo'].albedo_ir)

            # 7. thermal radiation
            if self.distribute['thermal'].gridded:
                self.distribute['thermal'].distribute_thermal(self.data.thermal.loc[t],
                                                              self.distribute['air_temp'].air_temp)
            else:
                self.distribute['thermal'].distribute(t,
                                                      self.distribute['air_temp'].air_temp,
                                                      self.distribute['vapor_pressure'].vapor_pressure,
                                                      self.distribute['vapor_pressure'].dew_point,
                                                      self.distribute['solar'].cloud_factor)

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
        :func:`smrf.data.loadTopo.topo` instance and the metadata loaded from
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
        #Create threads for distribution
        t,q = self.create_distributed_threads()

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

        # wait for all the threads to stop
#         for v in q:
#             q[v].join()

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
        for v in self.distribute:
            self.distribute[v].initialize(self.topo, self.data)

        # -------------------------------------
        # Create Queues for all the variables
        q = {}
        t = []

        self.thread_variables += ['storm_total']
        if self.distribute['precip'].nasde_model == 'marks2017':
            self.thread_variables += ['storm_id']

        if self.distribute['thermal'].correct_cloud:
            self.thread_variables += ['thermal_cloud']
        if self.distribute['thermal'].correct_veg:
            self.thread_variables += ['thermal_veg']

        for v in self.thread_variables:
            q[v] = queue.DateQueue_Threading(self.max_values, self.time_out)

        # -------------------------------------
        # Distribute the data

        # 0.1 sun angle for time step
        t.append(Thread(target=radiation.sunang_thread,
                        name='sun_angle',
                        args=(q, self.date_time,
                              self.topo.topoConfig['basin_lat'],
                              self.topo.topoConfig['basin_lon'],
                              0, 0, 0)))

        # 0.2 illumination angle
        t.append(Thread(target=radiation.shade_thread,
                        name='illum_angle',
                        args=(q, self.date_time,
                              self.topo.slope, self.topo.aspect)))

        # 1. Air temperature
        t.append(Thread(target=self.distribute['air_temp'].distribute_thread,
                        name='air_temp',
                        args=(q, self.data.air_temp)))

        # 2. Vapor pressure
        t.append(Thread(target=self.distribute['vapor_pressure'].distribute_thread,
                        name='vapor_pressure',
                        args=(q, self.data.vapor_pressure)))

        # 3. Wind_speed and wind_direction
        t.append(Thread(target=self.distribute['wind'].distribute_thread,
                        name='wind',
                        args=(q, self.data.wind_speed,
                              self.data.wind_direction)))

        # 4. Precipitation
        t.append(Thread(target=self.distribute['precip'].distribute_thread,
                        name='precipitation',
                        args=(q, self.data, self.date_time,
                                self.topo.mask)))

        # 5. Albedo
        t.append(Thread(target=self.distribute['albedo'].distribute_thread,
                        name='albedo',
                        args=(q, self.date_time)))

        # 6.1 Clear sky visible
        t.append(Thread(target=self.distribute['solar'].distribute_thread_clear,
                        name='clear_vis',
                        args=(q, self.data.cloud_factor, 'clear_vis')))

        # 6.2 Clear sky ir
        t.append(Thread(target=self.distribute['solar'].distribute_thread_clear,
                        name='clear_ir',
                        args=(q, self.data.cloud_factor, 'clear_ir')))

        # 6.3 Net radiation
        t.append(Thread(target=self.distribute['solar'].distribute_thread,
                        name='solar',
                        args=(q, self.data.cloud_factor)))

        # 7. thermal radiation
        if self.distribute['thermal'].gridded:
            t.append(Thread(target=self.distribute['thermal'].distribute_thermal_thread,
                            name='thermal',
                            args=(q, self.data.thermal)))
        else:
            t.append(Thread(target=self.distribute['thermal'].distribute_thread,
                            name='thermal',
                            args=(q, self.date_time)))

        return t,q

    def initializeOutput(self):
        """
        Initialize the output files based on the configFile section ['output'].
        Currently only :func:`NetCDF files <smrf.output.output_netcdf>` is supported.
        """

        if self.config['output']['frequency'] is not None:

            # check the out location
            pth = os.path.abspath(os.path.expanduser(
                self.config['output']['out_location']))
            if 'out_location' not in self.config['output']:
                raise Exception('''out_location must be specified
                                for variable outputs''')
            elif self.config['output']['out_location'] == 'WORKDIR':
                pth = os.environ['WORKDIR']
            elif not os.path.isdir(pth):
                os.makedirs(pth)

            self.config['output']['out_location'] = pth

            # frequency of outputs
            self.config['output']['frequency'] = \
                int(self.config['output']['frequency'])

            # determine the variables to be output
            self._logger.info('{} variables will be output'
                              .format(self.config['output']['variables']))

            output_variables = self.config['output']['variables']
#             output_variables = list(map(str.strip, output_variables))
            if not isinstance(output_variables, list):
                output_variables = output_variables.split(',')

            # determine which variables belong where
            variable_list = {}
            for v in output_variables:
                for m in self.modules:

                    if m in self.distribute.keys():

                        if v in self.distribute[m].output_variables.keys():

                            # if there is a key in the config file,
                            # then change the output file name
                            if v in self.config['output'].keys():
                                fname = os.path.join(self.config['output']['out_location'],
                                                     self.config['output'][v])
                            else:
                                fname = os.path.join(self.config['output']['out_location'],
                                                     v)

                            d = {'variable': v,
                                 'module': m,
                                 'out_location':fname,
                                 'info': self.distribute[m].output_variables[v]}
                            variable_list[v] = d

            # determine what type of file to output
            if self.config['output']['file_type'].lower() == 'netcdf':
                self.out_func = output.output_netcdf(variable_list, self.topo,
                                                     self.config['time'],
                                                     self.config['output'])

            elif self.config['output']['file_type'].lower() == 'hru':
                self.out_func = output.output_hru(variable_list, self.topo,
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
            current_time_step (date_time): the current time step datetime object

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
                # add only one variable to the output list and preceed as normal
                var_vals = [self.out_func.variable_list[out_var]]

            # Incomplete request
            elif module is not None or out_var is not None:
                raise ValueError('''Function requires an output module and
                                variable name when outputting a specific
                                variables''')

            else:
                # Output all the variables
                var_vals = self.out_func.variable_list.values()

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


def run_smrf(config_file):
    """
    Function that runs smrf how it should be operate for full runs.

    Args:
        config_file: string path to the config file
    """
    start = datetime.now()
    # initialize
    with SMRF(config_file) as s:
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

        #post process if necessary
        s.post_process()

        s._logger.info(datetime.now() - start)

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
