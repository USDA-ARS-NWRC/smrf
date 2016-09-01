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
dem_file = '/home/scotthavens/Documents/Projects/smrf/smrf/utils/wind/ned30m_brb.int.ipw'

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
dem = IPW(dem_file)
dem_data = dem.bands[0].data
x = dem.bands[0].x
y = dem.bands[0].y

# initialize the wind model with the dem
w = wind_model(x, y, dem_data, nthreads=12)

# calculate the maxus for the parameters and output to file
w.maxus(dmax, sepdist, inc, inst, save_file)

# window the maxus values based on the maxus values in the file
# w.windower(save_file, windower, 'maxus')



#------------------------------------------------------------------------------
# compare with the original outputs
# print 'loading comparison...'
# 
# 
# # for i,d in enumerate(w.directions):
# 
# i = 3
# m = nc.Dataset('/home/scotthavens/Documents/Projects/smrf/examples/maxus.nc')
# mxs = m.variables['maxus'][i,:]
# m.close()
# 
# # mxs = np.loadtxt('/media/Drobo1/BRB/BRB-wy09/spatial_WRF_OG/data/topo/maxus/maxus30m/maxus690_0.asc', skiprows=6)
# # mxs = np.loadtxt('/home/scotthavens/Documents/Projects/smrf/smrf/utils/wind/maxus_0.asc', skiprows=6)
# 
#   
# plt.imshow(w.maxus_val - mxs)
# plt.colorbar()
# plt.show()
# 
# # plt.plot(w.maxus_val[1,:] - mxs[1,:])
# # plt.show()
# 
# sz = (5000*5000)
# 
# H,xedges,yedges = np.histogram2d(np.reshape(w.maxus_val,sz), np.reshape(mxs,sz), bins=100)
# Hm = np.ma.masked_where(H == 0, H)
# im = plt.imshow(Hm, interpolation='nearest', origin='low',
#                 extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
# plt.show()

datetime.now() - start
