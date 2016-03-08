'''
2016-03-07 Scott Havens

Distributed forcing data over a grid using interpolation
'''

import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt

    
class GRID:
    '''
    Inverse distance weighting class
    - Standard IDW
    - Detrended IDW
    '''
    def __init__(self, config, mx, my, GridX, GridY, mz=None, GridZ=None, mask=None):
        
        """
        Args:
            config: configuration for grid interpolation
            mx: x locations for the points
            my: y locations for the points
            mz: z locations for the points
            GridX: x locations in grid to interpolate over
            GridY: y locations in grid to interpolate over
            GridZ: z locations in grid to interpolate over
            mask: mask for those points to include in the detrending
                will be ignored if config['mask'] is false
        """
               
        self.config = config
        
        # measurement point locations
        self.mx = mx
        self.my = my
        self.mz = mz
        self.npoints = len(mx)
        
        # grid information
        self.GridX = GridX
        self.GridY = GridY
        self.GridZ = GridZ
            
        # mask
        self.mask = np.zeros_like(self.mx, dtype=bool)
        if config['mask']:
            
            assert(mask.shape == GridX.shape)
            mask = mask.astype(bool)
            
            x = GridX[0,:]
            y = GridY[:,0]
            for i,v in enumerate(mx):
                xi = np.argmin(np.abs(x - mx[i]))
                yi = np.argmin(np.abs(y - my[i]))
                
                self.mask[i] = mask[yi,xi]
                
                
    def detrendedInterpolation(self, data, flag=0, method='linear'):
        """
        Interpolate using a detrended approach
        
        Args:
            data: data to interpolate
            method: scipy.interpolate.griddata interpolation method
        """
            
        # get the trend, ensure it's positive
        pv = np.polyfit(self.mz[self.mask].astype(float), data[self.mask], 1)
        if pv[0] >= 0:
            pv = np.array([0,0])
        
        # apply trend constraints
        if flag == 1 and pv[0] < 0:
            pv = np.array([0,0])
        elif (flag == -1 and pv[0] > 0):
            pv = np.array([0,0])
        
        self.pv = pv
        
        # detrend the data
        el_trend = self.mz * pv[0] + pv[1]
        dtrend = data - el_trend
        
        # interpolate over the DEM grid
        idtrend = griddata((self.mx,self.my), dtrend, (self.GridX,self.GridY), method=method)
        
        # retrend the data
        rtrend = idtrend + pv[0]*self.GridZ + pv[1]
        
        return rtrend
        
    
    def calculateInterpolation(self, data, method='linear'):
        """
        Interpolate over the grid
        
        Args:
            data: data to interpolate
            mx: x locations for the points
            my: y locations for the points
            X: x locations in grid to interpolate over
            Y: y locations in grid to interpolate over
        """
        
        
        g = griddata((self.mx,self.my), data, (self.GridX,self.GridY), method=method)
        
        return g
            

    
    
    
    
    
    

        
        
        