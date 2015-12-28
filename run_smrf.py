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

s = smrf.model.SMRF(configFile)     # initialize
s.loadTopo()
s.loadData()

print datetime.now() - start
