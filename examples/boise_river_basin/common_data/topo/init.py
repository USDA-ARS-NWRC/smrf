'''
Create the inital condition file

20160420 Scott Havens
'''

import os
from datetime import datetime

import netCDF4 as nc
import numpy as np

from smrf import ipw

startTime = datetime.now()

# location to save to
loc = './'

#------------------------------------------------------------------------------ 
# IPW stuff

u = 4920050
v = 550050
du = -100
dv = 100
units = 'm'
csys = 'UTM'
nx = 1500
ny = 1500

nbits = 16

# create the x,y vectors
x = v + dv*np.arange(nx)
y = u + du*np.arange(ny)

#------------------------------------------------------------------------------ 
# band 0 - DEM
d = ipw.IPW('dem.ipw')
dem = d.bands[0].data

#------------------------------------------------------------------------------ 
# band 1 - roughness length
rough = 0.005 * np.ones(dem.shape)

#------------------------------------------------------------------------------ 
# band 2 - total snowcover depth
depth = np.zeros(dem.shape)

#------------------------------------------------------------------------------ 
# band 3 - average snowcover density
density = np.zeros(dem.shape)

#------------------------------------------------------------------------------ 
# band 4 - active snow layer temperature
temp = np.zeros(dem.shape)

#------------------------------------------------------------------------------ 
# band 5 - average snowcover temperature
temp2 = np.zeros(dem.shape)

#------------------------------------------------------------------------------ 
# band 6 - percent of liquid H2O saturation
sat = np.zeros(dem.shape)


# # ouput to IPW
i = ipw.IPW()
i.new_band(dem)
i.new_band(rough)
i.new_band(depth)
i.new_band(density)
i.new_band(temp)
i.new_band(temp2)
i.new_band(sat)
i.add_geo_hdr([u, v], [du, dv], units, csys)
i.write('init.ipw', nbits)


print datetime.now() - startTime
