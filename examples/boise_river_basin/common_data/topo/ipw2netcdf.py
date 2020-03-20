"""
20161208 Scott Havens

Convert the IPW images for the topo input into a netCDF file
"""


from datetime import datetime

import netCDF4 as nc

from smrf import ipw

file_name = 'topo.nc'

f = {
     'dem': 'dem.ipw',
     'mask': 'mask.ipw',
     'veg_height': 'veg_height.ipw',
     'veg_k': 'veg_k.ipw',
     'veg_tau': 'veg_tau.ipw',
     'veg_type': 'veg_type.ipw'
     }

# get the x,y
d = ipw.IPW(f['dem'])
x = d.bands[0].x
y = d.bands[0].y

# create the netCDF file
s = nc.Dataset(file_name, 'w', format='NETCDF4', clobber=True)
                            
# add dimensions
dimensions = ['y', 'x']
s.createDimension(dimensions[0], y.shape[0])
s.createDimension(dimensions[1], x.shape[0])

# create the variables
s.createVariable('y', 'f', dimensions[0])
s.createVariable('x', 'f', dimensions[1])

# define some attributes
setattr(s.variables['y'], 'units', 'meters')
setattr(s.variables['y'], 'description', 'UTM, north south')
setattr(s.variables['x'], 'units', 'meters')
setattr(s.variables['x'], 'description', 'UTM, east west')

# define some global attributes
fmt = '%Y-%m-%d %H:%M:%S'
setattr(s, 'Conventions', 'CF-1.6')
setattr(s, 'dateCreated', datetime.now().strftime(fmt))
setattr(s, 'title', 'Distirbuted data from SMRF')
setattr(s, 'history', '[%s] Create netCDF4 file' % datetime.now().strftime(fmt))

s.variables['y'][:] = y
s.variables['x'][:] = x






for key,file_image in f.items():
    
    d = ipw.IPW(file_image)
    
    
    s.createVariable(key, 'f', (dimensions[0],dimensions[1]))
    s.variables[key][:] = d.bands[0].data




s.close()
