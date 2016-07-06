"""
Example script for running Adam Winstral's wind model

20160622 Scott Havens
"""

import smrf
import netCDF4 as nc
import matplotlib.pyplot as plt
import numpy as np

#------------------------------------------------------------------------------ 
# Specify model input parameters

# DEM file to read in
dem_file = '../test_data/topo/dem30m.ipw'

# middle upwind direction around which to run model (degrees)
angle = 180

# increment between direction calculations (degrees)
inc = 5

# length of outlying upwind search vector (meters)
dmax = 690

# length of local max upwind slope search vector (meters)
sepdist = 90

# Anemometer height (meters)
inst = 2

# Windower
windower = 30

#------------------------------------------------------------------------------
# run the wind model

# read in the DEM
dem = smrf.ipw.IPW(dem_file)
dem_data = dem.bands[0].data
x = dem.bands[0].x
y = dem.bands[0].y

w = smrf.utils.wind_model.wind_model(x, y, dem_data)

w.maxus(dmax, sepdist, inc, inst, 'smrf_maxus.nc')








#------------------------------------------------------------------------------
# compare with the original outputs

m = nc.Dataset('maxus.nc')

mxs = m.variables['maxus'][0,:]

plt.imshow(w.maxus_val - mxs)
plt.colorbar()
plt.show()
