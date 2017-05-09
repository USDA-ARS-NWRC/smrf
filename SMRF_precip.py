'''
20161114 Scott Havens

Distribute the point forcing data to the DEM
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
    configFile = 'BRB_precip_config.ini'
    if len(sys.argv) > 1:
        configFile = sys.argv[1]
    
    
    #===============================================================================
    # Model setup and initialize
    #===============================================================================
    #
    # These are steps that will load the necessary data and initialize the framework
    # Once loaded, this shouldn't need to be re-ran except if something major changes
    
    # 1. initialize
    s = smrf.framework.SMRF(configFile)
    
    # 2. load topo data
    s.loadTopo(calcInput=False)
    
    # 3. Create the distribution class
    s.distribute['precip'] = smrf.distribute.precipitation.ppt(s.config['precip'], s.config['time']['time_step'])
    
    # 4. load weather data  and station metadata
    s.loadData()
    
    # 5. initialize the outputs if desired
    s.initializeOutput()
    
    
    # 6. Initialize the distibution
    s.distribute['precip'].initialize(s.topo, s.data.metadata)
        
    # 7. Distribute the data
    for output_count,t in enumerate(s.date_time):
        s.distribute['precip'].distribute_precip(s.data.precip.ix[t])
        
        # output at the frequency and the last time step
        if (output_count % s.config['output']['frequency'] == 0) or (output_count == len(s.date_time)):
            s.output(t)
    
except Exception as e:
    s._logger.error(e)
    


s._logger.info(datetime.now() - start)
