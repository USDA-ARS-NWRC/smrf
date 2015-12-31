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
import logging
from datetime import datetime, timedelta
import pandas as pd
import itertools

from smrf import data, distribute


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

    def __init__(self, configFile, loglevel='INFO'):
        """
        Initialize the model, read config file, start and end date, and logging
        
        Args:
            configFile (str): path to configuration file
            loglevel (str): 
        
        Returns:
        
        """
        
        # read the config file and store
        f = MyParser()
        f.read(configFile)
        self.config = f.as_dict()
        
        # check for the desired sections
        if 'stations' not in self.config:
            self.config['stations'] = None
        
        # get the time section        
        self.start_date = pd.to_datetime(self.config['time']['start_date'])
        self.end_date = pd.to_datetime(self.config['time']['end_date'])
        self.date_time = data.mysql_data.date_range(self.start_date, self.end_date, timedelta(minutes=int(self.config['time']['time_step'])))
        
        
        # start logging
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
#         logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
        logging.basicConfig(level=numeric_level)
        self._loglevel = numeric_level
        
        self._logger = logging.getLogger(__name__)        
        self._logger.info('Started SMRF --> %s' % datetime.now())
        self._logger.info('Model start --> %s' % self.start_date)
        self._logger.info('Model end --> %s' % self.end_date)
        
        
    def __del__(self):
        """
        Provide some logging info about when SMRF was closed
        """
        self._logger.info('SMRF closed --> %s' % datetime.now())   
        
    
    def loadTopo(self):
        """
        load the topo data
        """
    
        # load the topo 
        self.topo = data.loadTopo.topo(self.config['topo'])
     
     
     
    def initializeDistribution(self):
        """
        This initializes the distirbution classes
        
        Loads all the necessary classes required for distributing the data
        into dictionary 'distribute' with variable names as the keys
        """
        
        self.distribute = {}
        
        self.distribute['air_temp'] = distribute.air_temp.ta(self.config['air_temp'])  # get the class
                
           
        
    def loadData(self):
        """
        Load the data
        """
        
        # get the start date and end date requested
        
        
        if 'csv' in self.config:
            self.data = data.loadData.wxdata(self.config['csv'], 
                                           self.start_date,
                                           self.end_date, 
                                           stations=self.config['stations'],
                                           dataType='csv')
            
        elif 'mysql' in self.config:
            self.data = data.loadData.wxdata(self.config['mysql'],
                                           self.start_date,
                                           self.end_date, 
                                           stations=self.config['stations'],
                                           dataType='mysql')
            
        else:
            raise KeyError('Could not determine where station data is located')   
        
  
        # ensure that the dataframes have consistent times
#         t = date_range(start_date, end_date, timedelta(minutes=m))
  
        # determine the locations of the stations on the grid
        
    
        
    def distributeData(self):
        """
        Distribute the data
        
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
        d = self._initDistributionDict(self.date_time, self.data.variables)
        
        #------------------------------------------------------------------------------
        # Initialize the distibution
        # 1. Air temperature
        self.distribute['air_temp'].initialize(self.topo, self.data.metadata)
        
        #------------------------------------------------------------------------------
        # Distribute the data
        for t in self.date_time:
            
            # wait here for the model to catch up if needed
            
            self._logger.debug('Distributing time step %s' % t)
        
            # 1. Air temperature 
            d[t]['air_temp'] = self.distribute['air_temp'].distribute(self.data.air_temp.ix[t])
            
        self.forcing_data = d
    
    def runModel(self):
        """
        Run the model
        """
        
        
        
        
        return True
    
    
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
        
    
