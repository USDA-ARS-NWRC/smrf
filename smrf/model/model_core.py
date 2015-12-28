'''
20151222 Scott Havens

Run the model given the configuration file that specifies what
modules to run, where the data comes from, and where the data 
is going

Steps:
1. Initialize model, load data
2. Distribute data
3. Run iSnobal when data is present
'''

import ConfigParser
import logging
from datetime import datetime

from smrf import data


class SMRF():

    def __init__(self, configFile):
        '''
        Initialize the model, load data, etc.
        '''
        self.hello = 'world'
        
        # read the config file and store
        f = MyParser()
        f.read(configFile)
        self.config = f.as_dict()
        
        # start logging
        # assuming loglevel is bound to the string value obtained from the
        # command line argument. Convert to upper case to allow the user to
        # specify --log=DEBUG or --log=debug
        loglevel = 'DEBUG' # self.config.system.log
        numeric_level = getattr(logging, loglevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
        logging.info('Started SMRF --> %s' % datetime.now())
        
        
    def __del__(self):
        '''
        Provide some logging info about when SMRF was closed
        '''
        logging.info('SMRF closed --> %s' % datetime.now())   
        
    
    def loadTopo(self):
        '''
        load the topo data
        '''
    
        # load the topo 
        self.topo = data.loadTopo.topo(self.config['topo'])
        
        
    def loadData(self):
        '''
        Load the data
        '''
        
        if 'csv' in self.config:
            print 'csv'
            
            
            
            
        elif 'mysql' in self.config:
            print 'mysql'
        else:
            raise KeyError('Could not determine where station data is located')
        
        return None
        
        
        
        
    def distributeData(self):
        '''
        Distribute the data
        use dagger to build the time step data and keep track of
        what file depends on another file
        '''
        
#         ta.generate()
        
    
    def runModel(self):
        '''
        Run the model
        '''
        return True
    
    
    
class MyParser(ConfigParser.ConfigParser):
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d
        
    
# def ConfigSectionMap(section):
#     dict1 = {}
#     options = Config.options(section)
#     for option in options:
#         try:
#             dict1[option] = Config.get(section, option)
#             if dict1[option] == -1:
#                 DebugPrint("skip: %s" % option)
#         except:
#             print("exception on %s!" % option)
#             dict1[option] = None
#     return dict1



