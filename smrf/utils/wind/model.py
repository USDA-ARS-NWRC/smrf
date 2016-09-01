"""
Cython implementation of Adam Winstral's wind model

20160623
"""

import numpy as np
import os
import netCDF4 as nc
import matplotlib.pyplot as plt
import progressbar
from datetime import datetime

import wind_c


class wind_model():
    
    def __init__(self, x, y, dem, nthreads=1):
        """
        Initialize with the dem
        """
        
        self.x = x
        self.y = y
        self.dem = dem
        self.nx = len(x)
        self.ny = len(y)
        self.ngrid = self.ny * self.nx
        self.nthreads = nthreads
        
        self.dx = np.abs(x[1] - x[0])
        self.dy = np.abs(y[1] - y[0])
        
        X,Y = np.meshgrid(np.arange(0, self.nx), np.arange(0, self.ny))
        self.X = X
        self.Y = Y
        self.shape = X.shape
        
                
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
#         swa = np.arange(-inc/2.0, 360-inc/2.0, inc)
        swa = np.arange(0, 360, inc)
        self.directions = swa    
#         swa = swa * np.pi / 180
        
        # initialize the output file
        self.out_file = out_file
        self.type = 'maxus'
        self.output_init(self.type, out_file)        
          
        
        # run model over range in wind directions
        for i,angle in enumerate(swa):
            
            self.maxus_val = self.maxus_angle(angle)
            self.output(self.type, i)
                        
            
            
            
    def maxus_angle(self, angle):
        """
        Calculate the maxus for a single direction
        """
        
        print "Calculating maxus for direction: %i" % (angle)
        
        angle *= np.pi / 180
        
        # calculate the endpoints
                
        # adjust for quatrants for going from bearing to cos/sin
        Xi = self.X + self.dmax_cell * np.cos(angle-np.pi/2)  
        Yi = self.Y + self.dmax_cell * np.sin(angle-np.pi/2)
        
        self.Xi = Xi.astype(np.int)
        self.Yi = Yi.astype(np.int)
        
        maxus = wind_c.call_maxus(self.x, self.y, self.dem, self.X, self.Y, 
                               self.Xi, self.Yi, self.inst_hgt, self.nthreads)
        
#         plt.imshow(mx)
#         plt.colorbar()
#         plt.show()
#         
#         maxus = np.zeros((self.ngrid,))
#         pbar = progressbar.ProgressBar(max_value=self.ngrid)
#         j = 0
#         for index in range(self.ngrid):
#             maxus[index] = self.find_maxus(index)
#             j += 1
#             pbar.update(j)
#             if j > 100000:
#                 break
#         pbar.finish()
#         maxus = np.reshape(maxus, self.shape)
        
        # correct for values that are their own horizon
        maxus[maxus <= -89.0] = 0
        
        return maxus
    
    
    def windower(self, maxus_file, window_width, wtype):
        """
        Take the maxus output and average over the window width
        
        Arg:
            maxus_file: location of the previously calculated maxus values
            window_width: window width about the wind direction
            wtype: type of wind calculation 'maxus' or 'tbreak'
            
        Return:
            New file containing the windowed values
        """
        
        
        # open the previous file and get the directions
        n = nc.Dataset(maxus_file, 'r')
        directions = n.variables['direction'][:]
        self.directions = directions
        
        
        # create a new file based on the old file
        name = os.path.splitext(maxus_file)
        out_file = "%s_%iwindow.nc" % (name[0], window_width)
        self.output_init(wtype, out_file)
        self.out_file = out_file
        
        
        # determine which directions are required for each single direction
        window_width /= 2
        inc = np.mean(np.diff(directions), dtype=int)
        
        
        
        for i,d in enumerate(directions):
            
            print "Windowing direction %i" % d
            
            # determine which directions to include
            window_start = d - window_width
            window_end = d + window_width
            sl = np.arange(window_start, window_end+1, inc) # to ensure that it contains the end points
            
            # correct for edge effects
            sl[sl < 0] = sl[sl < 0] + 360 
            sl[sl > 360] = sl[sl > 360] - 360
            
            # determine the indicies to the input file
            idx = self.ismember(directions, sl)
            
            # grab all the data for all directions and average
            self.maxus_val = np.mean(n.variables[wtype][idx,:], axis=0)
            
            # put it into the output file
            self.output(wtype, i)
            
            break
        
        n.close()
        
        
        
    def ismember(self, a, b):
        bind = {}
        for i, elt in enumerate(b):
            if elt not in bind:
                bind[elt] = True
        return [bind.get(itm, False) for itm in a] 
    
      
     
    def find_maxus(self, index):#, end_point):
        """
        Calculate the maxus given the start and end point
        
        Arg:
            start_point: tuple index for the start point
            end_point: tuple index for the end point
        """
        
        start_point = np.unravel_index(index, self.shape)
        
        # determine the points along the endpoint line
        end_point = (self.Yi[start_point], self.Xi[start_point])
        p = self.bresenham(start_point, end_point)
                        
        # ensure the cases where it's on the edge
        p = np.delete(p, np.where(p[:,0] < 0)[0], axis=0)
        p = np.delete(p, np.where(p[:,1] < 0)[0], axis=0)
        p = np.delete(p, np.where(p[:,0] > self.ny)[0], axis=0)
        p = np.delete(p, np.where(p[:,1] > self.nx)[0], axis=0)
            
        # determine the relative heights along the path 
        h = self.dem[p[:,1], p[:,0]] # - (self.inst_hgt + self.dem[index])
                    
        # find the horizon for each pixel along the path
        hord = self.hord(self.x[p[:,1]], self.y[p[:,0]], h)
        
        # calculate the angle to that point
        pt = p[hord[0],:]   # point that was found for horizon
        d = np.sqrt( np.power(self.x[pt[1]] - self.x[start_point[1]],2) + \
                    np.power(self.y[pt[0]] - self.y[start_point[0]],2) )
        
        slope = (h[hord[0]] - (h[0] + self.inst_hgt)) / d
        maxus = np.arctan(slope) * 180 / np.pi
        
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
    
    
    def hord(self, x, y, z):
        '''
        Calculate the horizon pixel for all z
        This mimics the simple algorthim from Dozier 1981 but
        was adapated for use in finding the maximum upwind slope
        
        Works backwards from the end but looks forwards for
        the horizon
        
        Args:
            z: elevations for the points
        
        Returns:
            h: index to the horizon point
        
        20150601 Scott Havens
        '''
        
        N = len(z)  # number of points to look at
    #     offset = 1      # offset from current point to start looking
        
        # preallocate the h array
        h = np.zeros(N, dtype=int)
        h[N-1] = N-1
        i = N - 2
        
        # work backwarks from the end for the pixels
        while i >= 0:
            h[i] = i
            j = i + 1   # looking forward
            found = False
            
            while found==False:
                
                d_i = np.sqrt( np.power(x[i] - x[j],2) + np.power(y[i] - y[j],2) )
                d_h = np.sqrt( np.power(x[i] - x[h[j]],2) + np.power(y[i] - y[h[j]],2) )
                
                pt_i = self._slope(0, z[i]+self.inst_hgt, d_i, z[j])
                pt_h = self._slope(0, z[i]+self.inst_hgt, d_h, z[h[j]])
                
                if (pt_i < pt_h):
                    if (j == N-1):
                        found = True
                        h[i] = j
                    else:
                        j = h[j]
                else:
                    found = True
                    if (pt_i > pt_h):
                        h[i] = j
                    else:
                        h[i] = h[j]
                
            i-=1
        
        return h
    
    def _slope(self, xi, zi, xj, zj):
        '''
        Slope between the two points
        20150603 Scott Havens
        '''
        
        return (zj - zi) / (xj - float(xi))
    
        
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
        
        