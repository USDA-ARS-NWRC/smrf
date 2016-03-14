"""
20151222 Scott Havens

Run the model given the configuration file that specifies what
modules to run, where the data comes from, and where the data 
is going

Steps:
1. Initialize model, load data
2. Distribute data
3. Run iSnobal when data is present
"""

import ConfigParser
import logging, os
from datetime import datetime, timedelta
import pandas as pd
# import itertools
import numpy as np
import pytz
import matplotlib.pyplot as plt

from smrf import data, distribute, model, output
from smrf.envphys import radiation


class SMRF():
    """
    SMRF - Snow Modeling Resources Framework
    
    Attributes:
        config: user configuration from config file
        start_date: start date for modeling and data
        end_date: end date for modeling and data
        date_time: numpy array of times start_date:time_step:end_date
        topo: smrf.data.loadTopo.topo instance to hold all data/info about the 
            dem, vegitation, and modeling domain
        data: smrf.data.loadData.wxdata instance to hold all the weather data
            loaded from either a CSV file or MySQL database
        
    """
    
    # These are the modules that the user can modify and use different methods
    modules = ['air_temp', 'albedo', 'precip', 'soil_temp', 'solar', 'thermal', 'vapor_pressure', 'wind']

    def __init__(self, configFile):
        """
        Initialize the model, read config file, start and end date, and logging
        
        Args:
            configFile (str): path to configuration file
            loglevel (str): 
        
        Returns:
        
        To-do:
        - Set default values for things and fill out the self.config dict
        
        """
        
        # read the config file and store
        if not os.path.isfile(configFile):
            raise Exception('Configuration file does not exist --> %s' % configFile)
        
        
        f = MyParser()
        f.read(configFile)
        self.config = f.as_dict()
        
        # check for the desired sections
        if 'stations' not in self.config:
            self.config['stations'] = None
            
        # if a gridded dataset will be used
        self.gridded = False
        if 'gridded' in self.config:
            self.gridded = True
            
        if 'nthreads_forcing' not in self.config['system']:
            self.config['system']['nthreads_forcing'] = 1
        if 'nthreads_isnobal' not in self.config['system']:
            self.config['system']['nthreads_isnobal'] = 1
                
        
        # get the time section        
        self.start_date = pd.to_datetime(self.config['time']['start_date'])
        self.end_date = pd.to_datetime(self.config['time']['end_date'])
        d = data.mysql_data.date_range(self.start_date, self.end_date,
                                       timedelta(minutes=int(self.config['time']['time_step'])))
        tzinfo = pytz.timezone(self.config['time']['time_zone'])
        self.date_time = [di.replace(tzinfo=tzinfo) for di in d]
        self.time_steps = len(self.date_time)    # number of time steps to model
        
        # check the temp dir
        if 'temp_dir' in self.config['system']:
            tempDir = self.config['system']['temp_dir']
        else:
            tempDir = os.environ['TMPDIR']
        self.tempDir = tempDir
        
        # start logging
        
        if 'log_level' in self.config['logging']:
            loglevel = self.config['logging']['log_level'].upper()
        else:
            loglevel='INFO'
            
        numeric_level = getattr(logging, loglevel, None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        
        
        logfile=None    
        if 'log_file' in self.config['logging']:
            logfile = self.config['logging']['log_file']

        if logfile is not None:
            logging.basicConfig(filename=logfile, filemode='w', level=numeric_level)
        else:
            logging.basicConfig(level=numeric_level)
            
        self._loglevel = numeric_level
        
        self._logger = logging.getLogger(__name__)        
        self._logger.info('Started SMRF --> %s' % datetime.now())
        self._logger.info('Model start --> %s' % self.start_date)
        self._logger.info('Model end --> %s' % self.end_date)
        self._logger.info('Number of time steps --> %i' % self.time_steps)
        
        # determine if this will be a restart
        restart = False
        if 'restart' in self.config['isnobal']:
            if self.config['isnobal']['restart'].lower == 'true':
                restart = True
        
        self.config['isnobal']['restart'] = restart
        
        
        
        
        
    def __del__(self):
        """
        Provide some logging info about when SMRF was closed
        """
        
        # clean up the TMPDIR
        os.remove(self.topo.stoporad_in_file)
        os.remove(self.distribute['solar'].vis_file)
        os.remove(self.distribute['solar'].ir_file)
        
        # close other files
        self.distribute['wind']._maxus_file.close()
        
#         # close output files
#         if self.out_func.type == 'netcdf':
#             for v in self.out_func.variable_list:
#                 v['nc_file'].close()
#                 self._logger.debug('Closed file: %s' % v['nc_file'])
        
        self._logger.info('SMRF closed --> %s' % datetime.now())   
        
    
    def loadTopo(self):
        """
        load the topo data
        """
    
        # load the topo 
        self.topo = data.loadTopo.topo(self.config['topo'], tempDir=self.tempDir)     
     
     
    def initializeDistribution(self):
        """
        This initializes the distirbution classes
        
        Loads all the necessary classes required for distributing the data
        into dictionary 'distribute' with variable names as the keys
        """
        
        self.distribute = {}
        
        # 1. Air temperature
        self.distribute['air_temp'] = distribute.air_temp.ta(self.config['air_temp'])  # get the class
        
        # 2. Vapor pressure
        self.distribute['vapor_pressure'] = distribute.vapor_pressure.vp(self.config['vapor_pressure'],
                                                                         self.config['system']['temp_dir'])
                
        # 3. Wind
        self.distribute['wind'] = distribute.wind.wind(self.config['wind'],
                                                       self.config['system']['temp_dir'])
        
        # 4. Precipitation
        self.distribute['precip'] = distribute.precipitation.ppt(self.config['precip'],
                                                                 self.config['time']['time_step'])
        
        # 5. Albedo
        self.distribute['albedo'] = distribute.albedo.albedo(self.config['albedo'])
        
        # 6. Solar radiation
        self.distribute['solar'] = distribute.solar.solar(self.config['solar'],
                                                          self.distribute['albedo'].config,
                                                          self.topo.stoporad_in_file,
                                                          self.config['system']['temp_dir'])
        
        # 7. thermal radiation
        self.distribute['thermal'] = distribute.thermal.th(self.config['thermal'])
        
        # 8. soil temperature
        self.distribute['soil_temp'] = distribute.soil_temp.ts(self.config['soil_temp'])
             
        
    def loadData(self):
        """
        Load the data
        """
        
        # get the start date and end date requested
        
        
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
            
        elif 'gridded' in self.config:
            self.data = data.loadGrid.grid(self.config['gridded'],
                                           self.topo,
                                           self.start_date,
                                           self.end_date,
                                           time_zone=self.config['time']['time_zone'],
                                           dataType='wrf',
                                           tempDir=self.tempDir)
            
        else:
            raise KeyError('Could not determine where station data is located')   
        
        # ensure that the dataframes have consistent times
#         t = date_range(start_date, end_date, timedelta(minutes=m))
  
        # determine the locations of the stations on the grid
        self.data.metadata['xi'] = self.data.metadata.apply(lambda row: find_pixel_location(row, self.topo.x, 'X'), axis=1)
        self.data.metadata['yi'] = self.data.metadata.apply(lambda row: find_pixel_location(row, self.topo.y, 'Y'), axis=1)
        
        
    def distributeData(self):
        """
        Distribute the measurement point data
        
        For now, do everything serial so that the process of distributing the 
        data is developed.  Once the methods are in place, then I can start
        playing with threads and running the distribution in parallel
        
        Future: use dagger to build the time step data and keep track of
        what file depends on another file
        
        Steps performed:
            1. Air temperature
            2. Vapor pressure
            3. Wind 
                3.1 Wind direction
                3.2 Wind speed
            4. Precipitation
            5. Solar
            6. Thermal
            7. Soil temperature
        
        
        To do:
            - All classes will have an intiialize and a distribute, with the same inputs
            - Then all can be initialized at once and all distributed at once
        """
        
        #------------------------------------------------------------------------------
        # initialize a dictionary to hold everything        
#         d = self._initDistributionDict(self.date_time, self.modules)
        
        
        #------------------------------------------------------------------------------
        # Initialize the distibution
        # 1. Air temperature
        self.distribute['air_temp'].initialize(self.topo, self.data.metadata)
        
        # 2. Vapor pressure
        self.distribute['vapor_pressure'].initialize(self.topo, self.data.metadata)
        
        # 3. Wind
        self.distribute['wind'].initialize(self.topo, self.data.metadata)
        
        # 4. Precipitation
        self.distribute['precip'].initialize(self.topo, self.data.metadata)
        
        # 5. Albedo
        self.distribute['albedo'].initialize(self.topo, self.data.metadata)
        
        # 6. Solar
        self.distribute['solar'].initialize(self.topo, self.data.metadata)
        
        # 7. thermal radiation
        self.distribute['thermal'].initialize(self.topo, self.data.metadata)
        
        # 8. Soil temperature
        self.distribute['soil_temp'].initialize(self.topo, self.data.metadata)
        
        #------------------------------------------------------------------------------
        # Distribute the data
        for output_count,t in enumerate(self.date_time):
            
            # wait here for the model to catch up if needed
            
            startTime = datetime.now()
            
            self._logger.info('Distributing time step %s' % t)
            
            # 0.1 sun angle for time step
            cosz, azimuth = radiation.sunang(t.astimezone(pytz.utc), 
                                            self.topo.topoConfig['basin_lat'],
                                            self.topo.topoConfig['basin_lon'],
                                            zone=0, slope=0, aspect=0)
            
            # 0.2 illumination angle
            illum_ang = None
            if cosz > 0:
                illum_ang = radiation.shade(self.topo.slope, self.topo.aspect, azimuth, cosz)
                    
        
            # 1. Air temperature 
            self.distribute['air_temp'].distribute(self.data.air_temp.ix[t])
            
            # 2. Vapor pressure
            self.distribute['vapor_pressure'].distribute(self.data.vapor_pressure.ix[t],
                                                        self.distribute['air_temp'].air_temp)
            
            # 3. Wind_speed and wind_direction
            self.distribute['wind'].distribute(self.data.wind_speed.ix[t],
                                               self.data.wind_direction.ix[t])
            
            # 4. Precipitation
            self.distribute['precip'].distribute(self.data.precip.ix[t],
                                                self.distribute['vapor_pressure'].dew_point,
                                                self.topo.mask)
            
            # 5. Albedo
            self.distribute['albedo'].distribute(t, illum_ang, self.distribute['precip'].storm_days)
            
            # 6. Solar
            self.distribute['solar'].distribute(self.data.cloud_factor.ix[t],
                                                illum_ang, 
                                                cosz, 
                                                azimuth,
                                                self.distribute['precip'].last_storm_day_basin,
                                                self.distribute['albedo'].albedo_vis,
                                                self.distribute['albedo'].albedo_ir)
            
            # 7. thermal radiation
            if self.distribute['thermal'].gridded:
                self.distribute['thermal'].distribute_thermal(self.data.thermal.ix[t])
            else:
                self.distribute['thermal'].distribute(self.distribute['air_temp'].air_temp,
                                                      self.distribute['vapor_pressure'].dew_point,
                                                      self.distribute['solar'].cloud_factor)
                
            # 8. Soil temperature
            self.distribute['soil_temp'].distribute()
            
            
            # output at the frequency and the last time step
            if (output_count % self.config['output']['frequency'] == 0) or (output_count == len(self.date_time)):
                self.output(t)
            
#             plt.imshow(self.distribute['albedo'].albedo_vis), plt.colorbar(), plt.show()
            
            
            # pull all the images together to create the input image
#             d[t]['air_temp'] = self.distribute['air_temp'].image
#             d[t]['vapor_pressure'] = self.distribute['vapor_pressure'].image 
            
            
            # check if out put is desired
            
            telapsed = datetime.now() - startTime
            self._logger.debug('%.1f seconds for time step' % telapsed.total_seconds())
            
        self.forcing_data = 1
    
    
    
    def initializeOutput(self):
        """
        Initialize the output files
        
        """
        
        if self.config['output']['frequency'] is not None:
                
            # check the out location   
            pth = os.path.abspath(os.path.expanduser(self.config['output']['out_location'])) 
            if 'out_location' not in self.config['output']:
                raise Exception('out_location must be specified for variable outputs')
            elif self.config['output']['out_location'] == 'TMPDIR':
                pth = os.environ['TMPDIR']
            elif not os.path.isdir(pth):
                os.makedirs(pth)
                
            self.config['output']['out_location'] = pth
            
            # frequency of outputs
            self.config['output']['frequency'] = int(self.config['output']['frequency'])
            
            
            # determine the variables to be output
            self._logger.info('%s variables will be output' % self.config['output']['variables'])
            
            output_variables = self.config['output']['variables'].split(',')
            output_variables = map(str.strip, output_variables)
            
            # determine which variables belong where
            variable_list = {}
            for v in output_variables:
                for m in self.modules:
                
                    if v in self.distribute[m].output_variables.keys():
                        fname = os.path.join(self.config['output']['out_location'], v)
                        d = {'variable': v, 'module': m, 'out_location': fname, 'info': self.distribute[m].output_variables[v]}
                        variable_list[v] = d

            
            # determine what type of file to output    
            if self.config['output']['file_type'].lower() == 'netcdf':
                self.out_func = output.output_netcdf(variable_list, self.topo,
                                                     self.config['time'],
                                                     self.config['output']['frequency'])
            
            else:
                raise Exception('Could not determine type of file for output')
             
        else:
            self._logger.info('No variables will be output')
            self.output_variables = None
    
    
    
    def output(self, current_time_step):
        """
        Output the forcing data or model outputs
        
        Args:
            current_time_step: the current time step datetime object
        """
        
        # get the output variables then pass to the function
        for v in self.out_func.variable_list.values():
            
            # get the data desired
            data = getattr(self.distribute[v['module']], v['variable'])
            
            if data is None:
                data = np.zeros((self.topo.ny, self.topo.nx))
            
            # output the time step
            self.out_func.output(v['variable'], data, current_time_step)
            
    
    def initializeModel(self):
        """
        Initialize the models
        """   
        
        self.model = {}
        
        self.model['isnobal'] = model.isnobal(self.config['isnobal'], self.topo)
        
    
    def runModel(self):
        """
        Run the model
        """
        
        self.model['isnobal'].runModel()
    
    
    def _initDistributionDict(self, date_time, variables):
        """
        Create a dictionary to hold all the data.  They keys will be datetime objects
        with each one holding all the necessary variables for that timestep
        
        d = {
            datetime.datetime(2008, 10, 1, 1, 0): {
                'air_temp':{},
                'vapor_pressure':{},
                ...
            },
            datetime.datetime(2008, 10, 1, 2, 0): {
                'air_temp':{},
                'vapor_pressure':{},
                ...
            },
            ...
        }
        
        Args:
            date_time: list/array of Timestamp or datetime objects
            variables: list of variables under each time
            
        Return:
            d: dictionary
        """
        
        d = {}
        b = {}
        
        for v in variables:
            b[v] = []
        
        for k in date_time:
            d[k] = dict(b)
            
        return d  
        
    
    
class MyParser(ConfigParser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        d = self._make_lowercase(d)
        return d
    
    def _make_lowercase(self, obj):
        if hasattr(obj,'iteritems'):
            # dictionary
            ret = {}
            for k,v in obj.iteritems():
                ret[self._make_lowercase(k)] = v
            return ret
        elif isinstance(obj,basestring):
            # string
            return obj.lower()
        elif hasattr(obj,'__iter__'):
            # list (or the like)
            ret = []
            for item in obj:
                ret.append(self._make_lowercase(item))
            return ret
        else:
            # anything else
            return obj
        
        
        
def find_pixel_location(row, vec, a):
        """
        Find the index of the stations X/Y location in the model domain
        """   
        return np.argmin(np.abs(vec - row[a]))
        
    
