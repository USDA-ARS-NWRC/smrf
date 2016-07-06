'''
20151119 Scott Havens

Create a netCDF file from the maxus files
'''

import numpy as np
import os, glob
from smrf import ipw
import netCDF4 as nc
import re
import progressbar
# import multiprocessing as mp

from datetime import datetime
startTime = datetime.now()

maxus_dir = './maxus100m/maxus690_100.*.asc'

maxus_dir = '/media/Drobo1/BRB/BRB-wy09/spatial_WRF_OG/data/topo/maxus/maxus30m/'

maxus_file = 'maxus690__30.%i.asc'
var = 'maxus'
nFile = 'maxus_window.nc'

# maxus_file = 'tbreak90_%i.asc'
# var = 'tbreak'
# nFile = 'tbreak.nc'

maxusInd = range(0, 360, 5)

#------------------------------------------------------------------------------ 
# include the geohdr
# execfile('/media/Drobo1/BRB/BRB-wy09/grid_info.py')
dem = '/media/Drobo1/BRB/BRB-wy09/spatial_WRF_OG/data/topo/dem30m.ipw'
dem = ipw.IPW(dem)

nx = dem.nsamps
ny = dem.nlines
v = dem.bands[0].bsamp
dv = dem.bands[0].dsamp
u = dem.bands[0].bline
du = dem.bands[0].dline


# files = glob.glob(maxus_dir)
nfiles = len(maxusInd)

#===============================================================================
# Create netCDF file
#===============================================================================
 
dimensions = ('Direction','y','x')
 
s = nc.Dataset(nFile, 'w', 'NETCDF4')
 
s.createDimension(dimensions[0], nfiles)
s.createDimension(dimensions[1], ny)
s.createDimension(dimensions[2], nx)
 
# create the variables
s.createVariable('direction', 'i', dimensions[0])
s.createVariable('y', 'f', dimensions[1])
s.createVariable('x', 'f', dimensions[2])
s.createVariable(var, 'f', dimensions)
 
# define some attributes
setattr(s.variables['y'], 'units', 'meters')
setattr(s.variables['y'], 'description', 'UTM, north south')
setattr(s.variables['x'], 'units', 'meters')
setattr(s.variables['x'], 'description', 'UTM, east west')
setattr(s.variables['direction'], 'units', 'bearing')
setattr(s.variables['direction'], 'description', 'Wind direction from North')
setattr(s.variables[var], 'units', 'angle')
setattr(s.variables[var], 'description', 'Maximum upwind slope')
setattr(s, 'dateCreated', startTime.isoformat())
 
# create the x,y vectors
x = v + dv*np.arange(nx)
y = u + du*np.arange(ny)
 
s.variables['y'][:] = y
s.variables['x'][:] = x
 


#===============================================================================
# Read in files
#===============================================================================
# read in the maxus files


# maxus = np.empty((ny, nx, nfiles))
# maxusInd = np.empty(nfiles)
pbar = progressbar.ProgressBar(max_value=nfiles).start()
 
# # get all the file names and sort
# for i,filename in enumerate(files):
#     dir = int(re.split('\.',filename)[-2])
#     maxusInd[i] = dir
#      
# indSorted = np.argsort(maxusInd)
# maxusInd = maxusInd[indSorted]
# filesSorted = [files[i] for i in indSorted]
 
s.variables['direction'][:] = maxusInd

j = 0
for d,i in enumerate(maxusInd):
    filename = maxus_dir + maxus_file % i
    if os.path.getsize(filename) > 10000:
        p = np.loadtxt(filename, skiprows=6)
#         p = i*np.ones((ny,nx))
        s.variables[var][d,:] = p
    pbar.update(j)
    j+=1
    s.sync()
pbar.finish()

s.close()

print datetime.now() - startTime





