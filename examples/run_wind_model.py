"""
Example script for running Adam Winstral's wind model

20160622 Scott Havens
"""

from smrf.utils.wind.model import wind_model
from smrf.ipw import IPW
import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime
start = datetime.now()

import faulthandler

faulthandler.enable()

#------------------------------------------------------------------------------ 
# Specify model input parameters

# DEM file to read in
dem_file = '../test_data/topo/dem30m.ipw'
dem_file = '/home/scotthavens/Documents/Projects/smrf/test_data/topo/dem30m.ipw'
# dem_file = '/home/scotthavens/Documents/Projects/smrf/smrf/utils/wind/ned30m_brb.ipw'

# # middle upwind direction around which to run model (degrees)
# angle = 180

# increment between direction calculations (degrees)
inc = 5

# length of outlying upwind search vector (meters)
dmax = 690

# length of local max upwind slope search vector (meters)
sepdist = 90

# Anemometer height (meters)
inst = 3

# Windower
windower = 30

save_file = '/home/scotthavens/Documents/Projects/smrf/examples/smrf_maxus.nc'
save_file2 = '/home/scotthavens/Documents/Projects/smrf/examples/smrf_tbreak.nc'

#------------------------------------------------------------------------------
# run the wind model

# read in the DEM
dem = IPW(dem_file)
# dem_data = np.round(dem.bands[0].data)
dem_data = dem.bands[0].data
x = dem.bands[0].x
y = dem.bands[0].y

# initialize the wind model with the dem
w = wind_model(x, y, dem_data, nthreads=12)

# calculate the maxus for the parameters and output to file
w.maxus(dmax, inc, inst, save_file)
print datetime.now() - start

# window the maxus values based on the maxus values in the file
w.windower(save_file, windower, 'maxus')

# calculate the maxus for the parameters and output to file
# w.tbreak(dmax, sepdist, inc, inst, save_file2)


print datetime.now() - start
