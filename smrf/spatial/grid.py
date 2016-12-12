'''
2016-03-07 Scott Havens

Distributed forcing data over a grid using interpolation
'''
__version__ = '0.0.1'

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
        
        
#         # create a plot for the DOCS
#         fs = 16
#         fw = 'bold'
#         xi = np.array([500, 3000])
#         yi = pv[0]*xi + self.pv[1] 
#         fig = plt.figure(figsize=(24,9))        
#           
#         extent = (np.min(self.GridX), np.max(self.GridX), np.min(self.GridY), np.max(self.GridY))
#         # elevational trend
#         ax0 = plt.subplot(1,3,1)
#         plt.plot(self.mz, data, 'o', xi, yi, 'k', linewidth=2)
#         plt.text(2000, 10, 'Slope: %f' % self.pv[0], fontsize=fs, fontweight=fw)
#         plt.xlabel('Elevation [m]', fontsize=fs, fontweight=fw)
#         plt.ylabel('Air Temperature [C]', fontsize=fs, fontweight=fw)       
#         ax0.set_ylim(-5, 12)       
#           
#         ax1 = plt.subplot(1,3,2)
#         im1 = ax1.imshow(idtrend, aspect='equal',extent=extent)
# #         plt.plot(self.mx, self.my, 'o')
#         plt.title('Distributed Residuals', fontsize=fs, fontweight=fw)
#         cbar = plt.colorbar(im1, orientation="horizontal")
#         cbar.ax.tick_params(labelsize=fs-2) 
#         plt.tick_params(
#             axis='both',          # changes apply to the x-axis
#             which='both',      # both major and minor ticks are affected
#             bottom='off',      # ticks along the bottom edge are off
#             top='off',         # ticks along the top edge are off
#             left='off',
#             right='off',
#             labelleft='off',
#             labelbottom='off') # labels along the bottom edge are off
#         ax1.set_xlim(extent[0], extent[1])
#         ax1.set_ylim(extent[2], extent[3])
#           
#           
#         # retrended     
#         ax2 = plt.subplot(133)
#         im2 = ax2.imshow(rtrend, aspect='equal',extent=extent)
# #         plt.plot(self.mx, self.my, 'o')
#         plt.title('Retrended by Elevation', fontsize=fs, fontweight=fw)
#         cbar = plt.colorbar(im2, orientation="horizontal")
#         cbar.ax.tick_params(labelsize=fs-2)
#         plt.tick_params(
#             axis='both',          # changes apply to the x-axis
#             which='both',      # both major and minor ticks are affected
#             bottom='off',      # ticks along the bottom edge are off
#             top='off',         # ticks along the top edge are off
#             left='off',
#             right='off',
#             labelleft='off',
#             labelbottom='off') # labels along the bottom edge are off
#         ax2.set_xlim(extent[0], extent[1])
#         ax2.set_ylim(extent[2], extent[3])
#                    
#         for item in ([ax0.xaxis.label, ax0.yaxis.label] +
#                      ax0.get_xticklabels() + ax0.get_yticklabels()):
#             item.set_fontsize(fs)
#             item.set_fontweight(fw) 
#                    
#         plt.tight_layout()
#         plt.show()
        
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
            

    
    
    
    
    
    

        
        
        
