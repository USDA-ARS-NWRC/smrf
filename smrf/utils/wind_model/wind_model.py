"""
Python implementation of Adam Winstral's wind model

20160623
"""

import numpy as np
from smrf.envphys import radiation
import netCDF4 as nc
import matplotlib.pyplot as plt
import progressbar
from datetime import datetime


class wind_model():
    
    def __init__(self, x, y, dem):
        """
        Initialize with the dem
        """
        
        self.x = x
        self.y = y
        self.dem = dem
        self.nx = len(x)
        self.ny = len(y)
        
        self.dx = np.abs(x[1] - x[0])
        self.dy = np.abs(y[1] - y[0])
        
                
    def maxus(self, dmax, sepdist, inc=5, inst=2, out_file='smrf_maxus.nc'):
        """
        Calculate the maxus values
        
        Args:
            dmax: length of outlying upwind search vector (meters)
            sepdist: length of local max upwind slope search vector (meters)
            angle: middle upwind direction around which to run model (degrees)
            inc: increment between direction calculations (degrees)
            inst: Anemometer height (meters)
        """
        
        if (sepdist % self.dx != 0) | (dmax % self.dx != 0):
            raise ValueError('sepdist and dmax must divide evenly into the DEM')
                               
                
        self.dmax = dmax
        self.dmax_cell = dmax / self.dx # the number of cells that dmax covers
        self.sepdist = sepdist
        self.inc = inc
        self.inst_hgt = inst
                
        # All angles that model will consider.
#         swa = np.arange(-inc/2, 360-inc/2, inc)
        swa = np.arange(0, 360, inc)
        self.directions = swa
        swa -= 90                       # adjust for quatrants, as well as 0deg to the East
        swa[swa<0] = swa[swa<0]+360     
        swa = swa * np.pi / 180
        
        # initialize the output file
        self.out_file = out_file
        self.type = 'maxus'
        self.output_init(self.type, out_file)        
          
        
        # run model over range in wind directions
        for i,angle in enumerate(swa):
            
            self.maxus_val = self.maxus_angle(angle)
            self.output(self.type, i)
            break
            
            
            
    def maxus_angle(self, angle):
        """
        Calculate the maxus for a single direction
        """
        
        print "Calculating maxus for direction: %i" % (angle*180/np.pi)
        
        # calculate the endpoints
        X,Y = np.meshgrid(np.arange(0, self.nx), np.arange(0, self.ny))
        
        Xi = X + self.dmax_cell * np.cos(angle)
        Yi = Y + self.dmax_cell * np.sin(angle)
        
        Xi = Xi.astype(np.int)
        Yi = Yi.astype(np.int)
        
        maxus = np.zeros(X.shape)
        
        # calcualte the maximum upwind slope value
        pbar = progressbar.ProgressBar(max_value=self.nx*self.ny)
        j = 0
        for index,val in np.ndenumerate(self.dem):
#             print index
#             index = (1,0)
            
            # determine the points along the endpoint line
            p = self.bresenham(index, (Yi[index], Xi[index]))
            
#             if p.size != 0:
                
            # ensure the cases where it's on the edge
            p = np.delete(p, np.where(p[:,0] < 0)[0], axis=0)
            p = np.delete(p, np.where(p[:,1] < 0)[0], axis=0)
            p = np.delete(p, np.where(p[:,0] > self.ny)[0], axis=0)
            p = np.delete(p, np.where(p[:,1] > self.nx)[0], axis=0)
                
#                 not_edge = True
#             else:
#                 not_edge = False
#                 maxus[index] = 0
            
            
#             if not_edge:
        
            # determine the relative heights along the path 
            h = self.dem[p[:,1], p[:,0]] - (self.inst_hgt + self.dem[index])
            
            # find the horizon for each pixel along the path
            hord = radiation.hord(h)
            
            # calculate the angle to that point
            pt = [p[hord[0],0], p[hord[0],1]]   # point that was found for horizon
            d = np.sqrt( np.power(self.x[pt[0]] - self.x[index[1]],2) + \
                        np.power(self.y[pt[1]] - self.y[index[0]],2) )
            
            maxus[index] = np.arctan(h[hord[0]] / d) / np.pi * 180
        
        
            j += 1
            pbar.update(j)
            
            if j > 1000000:
                break
            
        pbar.finish()
        
        # correct for values that are their own horizon
        maxus[maxus == -90.0] = 0
        
        return maxus
        
        
        
    def bresenham(self, start, end):
#         start = list(start)
#         end = list(end)
        path = []
        
#         steep = abs(end[1]-start[1]) > abs(end[0]-start[0])
        
        x0 = start[0]
        y0 = start[1]
        x1 = end[0]
        y1 = end[1]
        
        steep = abs(y1 - y0) > abs(x1 - x0)
        backward = x0 > x1
    
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if backward:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
    
        dx = x1 - x0
        dy = abs(y1 - y0)
        error = dx / 2
        y = y0
    
        if y0 < y1: 
            ystep = 1 
        else: 
            ystep = -1
        
        for x in range(x0, x1+1):
            if steep:
                path.append((y,x))
            else:
                path.append((x,y))
            
            error -= dy
            
            if error <= 0:
                y += ystep
                error += dx
                
        if backward: 
            path.reverse()
        
        return np.array(path)
    
    
    
        
    def output_init(self, ptype, filename):
        """
        Write the type out to netCDF
        """
        
        if ptype == 'maxus':
            var = 'maxus'
            desc = 'Maximum upwind slope'
            
        elif ptype == 'tbreak':
            var = 'tbreak'
            desc = 'tbreak'
            
        else:
            raise ValueError('Could not determine what to output, check type value (maxus or tbreak)')
        
        
        dimensions = ('Direction','y','x')
 
        s = nc.Dataset(filename, 'w', 'NETCDF4')
         
        s.createDimension(dimensions[0], len(self.directions))
        s.createDimension(dimensions[1], self.ny)
        s.createDimension(dimensions[2], self.nx)
         
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
        setattr(s.variables[var], 'description', desc)
        setattr(s, 'dateCreated', datetime.now().isoformat())
        
        s.variables['y'][:] = self.y
        s.variables['x'][:] = self.x
        
        
    
    def output(self, ptype, index):
                 
        s = nc.Dataset(self.out_file, 'r+')
        
        s.variables['direction'][:] = self.directions
        
        s.variables[ptype][index,:] = self.maxus_val
        
        s.close()
        
        