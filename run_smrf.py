'''
20151222 Scott Havens

run_smrf.py is a command line program meant to take a single
argument for the config file.  From this program, smrf.model
will be loaded to run the full program.

Users can also run the model as they want by using the smrf.model.SMRF
class to change things or whatever
'''

import smrf
from datetime import datetime

start = datetime.now()

# read config file
# create a new model instance
# initialize the model
# run the model
# output if necessary

configFile = './data/testConfig.ini'


#===============================================================================
# Model setup and initialize
#===============================================================================
#
# These are steps that will load the necessary data and initialize the framework
# Once loaded, this shouldn't need to be re-ran except if something major changes

# 1. initialize
s = smrf.model.SMRF(configFile, loglevel='debug')

# 2. load topo data
s.loadTopo()

# 3. initialize the distribution
s.initializeDistribution()


#===============================================================================
# Distribute data
#===============================================================================
#
# Once the framework is setup, we can load data and distribute the data
# This can be ran multiple times while the framework is running so that the
# intialization doesn't have to be re-ran, i.e. if this becomes a GUI


# 4. load weather data  and station metadata
s.loadData()

# 5. distribute  

s.distributeData()

#===============================================================================
# Run model
#===============================================================================


print datetime.now() - start
