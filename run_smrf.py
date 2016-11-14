'''
20151222 Scott Havens

run_smrf.py is a command line program meant to take a single
argument for the config file.  From this program, smrf.framework
will be loaded to run the full program.

Users can also run the model as they want by using the smrf.framework.SMRF
class to change things or whatever
'''

import smrf
from datetime import datetime
import sys
import faulthandler

faulthandler.enable()

start = datetime.now()

# read config file
# create a new model instance
# initialize the model
# run the model
# output if necessary

try:
    configFile = './test_data/testConfig.ini'
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    
    
    #===============================================================================
    # Model setup and initialize
    #===============================================================================
    #
    # These are steps that will load the necessary data and initialize the framework
    # Once loaded, this shouldn't need to be re-ran except if something major changes
    
    # 1. initialize
    with smrf.framework.SMRF(configFile) as s:
    
        # 2. load topo data
        s.loadTopo()
        
        # 3. initialize the distribution
        s.initializeDistribution()
        
        # initialize the outputs if desired
        s.initializeOutput()
        
        # 4. Initialize the model
        # s.initializeModel()
        
        
        #===============================================================================
        # Distribute data
        #===============================================================================
        #
        # Once the framework is setup, we can load data and distribute the data
        # This can be ran multiple times while the framework is running so that the
        # intialization doesn't have to be re-ran, i.e. if this becomes a GUI
        
        
        # 5. load weather data  and station metadata
        s.loadData()
        
        # 6. distribute
        s.distributeData()
        
        #===============================================================================
        # Run model
        #===============================================================================
        
        # 7. run the model
        # s.runModel()

except Exception as e:
    #print 'Error: %s' % e
    s._logger.error(e)
    
    
s._logger.info(datetime.now() - start)
