import os
from datetime import datetime

import netCDF4 as nc
import numpy as np
import pandas as pd

from smrf.envphys.phys import satvp

input_file = '../../tests/RME/gridded/WRF_test.nc'
output_file = '../../tests/RME/gridded/netcdf_test.nc'

if os.path.isfile(output_file):
    os.remove(output_file)

#===============================================================================
# Create netCDF file
#===============================================================================

dimensions = ('time','latitude','longitude')
 
i = nc.Dataset(input_file, 'r')
o = nc.Dataset(output_file, 'w')
 
 
tm = i.variables['Times'].shape[0]
ny,nx = i.variables['HGT'].shape
o.createDimension(dimensions[0], tm)
o.createDimension(dimensions[1], ny)
o.createDimension(dimensions[2], nx)

#===============================================================================
# TIME
#===============================================================================

o.createVariable('time', 'f', dimensions[0])

# convert the time from WRF to CF compliant
t = i.variables['Times']
t.set_auto_maskandscale(False)
try:
    times = [('').join(v) for v in t]
except TypeError:
    times = []
    for v in t:
        times.append(''.join([s.decode('utf-8') for s in v]))
        
times = [v.replace('_', ' ') for v in times]  # remove the underscore
time = pd.to_datetime(times)

# define some attributes
o.variables['time'].setncattr(
        'units',
        'hours since {}'.format(time[0].isoformat(' ')))
o.variables['time'].setncattr(
        'calendar',
        'standard')
o.variables['time'].setncattr(
        'long_name',
        'time')

h = [nc.date2num(tt,
                o.variables['time'].units,
                o.variables['time'].calendar)
     for tt in time]
o.variables['time'][:] = h

#===============================================================================
# DEM vars
#===============================================================================

o.createVariable('lat', 'f', dimensions[1:])
o.createVariable('lon', 'f', dimensions[1:])
o.createVariable('elev', 'f', dimensions[1:])

o.variables['lat'][:] = i.variables['XLAT'][:]
o.variables['lon'][:] = i.variables['XLONG'][:]
o.variables['elev'][:] = i.variables['HGT'][:]

#===============================================================================
# air temp
#===============================================================================

o.createVariable('air_temp', 'f', dimensions)
o.variables['air_temp'].setncattr('units', 'Celcius')
o.variables['air_temp'][:] = i.variables['T2'][:] - 273.15

#===============================================================================
# vapor pressure
#===============================================================================

o.createVariable('vapor_pressure', 'f', dimensions)
o.variables['vapor_pressure'].setncattr('units', 'Pascals')
o.variables['vapor_pressure'][:] = satvp(i.variables['DWPT'][:])

#===============================================================================
# precipitation
#===============================================================================

o.createVariable('precip', 'f', dimensions)
o.variables['precip'].setncattr('units', 'mm')
ppt = np.diff(i.variables['RAINNC'][:], axis=0)
o.variables['precip'][:] = np.concatenate((np.zeros((1,ny,nx)), ppt), axis=0)
 
#===============================================================================
# wind speed and direction
#===============================================================================

ugrd = i.variables['UGRD'][:]
vgrd = i.variables['VGRD'][:]

# convert to direction and speed
# calculate the wind speed
s = np.sqrt(ugrd**2 + vgrd**2)

# calculate the wind direction
d = np.degrees(np.arctan2(vgrd, ugrd))

ind = d < 0
d[ind] = d[ind] + 360

o.createVariable('wind_speed', 'f', dimensions)
o.variables['wind_speed'].setncattr('units', 'm/s')
o.variables['wind_speed'][:] = s

o.createVariable('wind_direction', 'f', dimensions)
o.variables['wind_direction'].setncattr('units', 'degrees')
o.variables['wind_direction'][:] = d

#===============================================================================
# cloud factor
#===============================================================================

o.createVariable('cloud_factor', 'f', dimensions)
o.variables['cloud_factor'].setncattr('units', 'None')
cf = np.mean(i.variables['CLDFRA'][:], axis=1)
o.variables['cloud_factor'][:] = 1 - cf

#===============================================================================
# thermal
#===============================================================================

o.createVariable('thermal', 'f', dimensions)
o.variables['thermal'].setncattr('units', 'W/m2')
o.variables['thermal'][:] = i.variables['GLW'][:]


# define some global attributes
o.setncattr_string('dateCreated', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
o.setncattr_string('title', 'Test generic NetCDF for SMRF')
o.setncattr_string('institution',
        'USDA Agricultural Research Service, Northwest Watershed Research Center')
o.setncattr_string('references',
        'Online documentation smrf.readthedocs.io; https://doi.org/10.1016/j.cageo.2017.08.016')



i.close()
o.close()
