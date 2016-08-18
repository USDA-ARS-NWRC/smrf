"""
Example script for running Adam Winstral's wind model

20160622 Scott Havens
"""

import smrf
import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np

from datetime import datetime
start = datetime.now()


#------------------------------------------------------------------------------ 
# Specify model input parameters

# DEM file to read in
dem_file = '../test_data/topo/dem30m.ipw'
dem_file = '/home/scotthavens/Documents/Projects/smrf/test_data/topo/dem30m.ipw'

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

#------------------------------------------------------------------------------
# run the wind model

# read in the DEM
dem = smrf.ipw.IPW(dem_file)
dem_data = dem.bands[0].data
x = dem.bands[0].x
y = dem.bands[0].y

# initialize the wind model with the dem
w = smrf.utils.wind_model.wind_model(x, y, dem_data, nthreads=8)

# calculate the maxus for the parameters and output to file
w.maxus(dmax, sepdist, inc, inst, save_file)

# window the maxus values based on the maxus values in the file
# w.windower(save_file, windower, 'maxus')



#------------------------------------------------------------------------------
# compare with the original outputs

m = nc.Dataset('/home/scotthavens/Documents/Projects/smrf/examples/maxus.nc')
mxs = m.variables['maxus'][0,:]
m.close()

# mxs = np.loadtxt('/media/Drobo1/BRB/BRB-wy09/spatial_WRF_OG/data/topo/maxus/maxus30m/maxus690_0.asc', skiprows=6)

  
# plt.imshow(w.maxus_val - mxs)
# plt.colorbar()


plt.show()


datetime.now() - start
