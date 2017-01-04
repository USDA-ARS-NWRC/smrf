'''
2015-11-30 Scott Havens
updated 2015-12-31 Scott Havens
    - start using panda dataframes to help keep track of stations 

Distributed forcing data over a grid using different methods
'''
__version__ = '0.1.1'

import numpy as np
# import sheppard
import matplotlib.pyplot as plt
    
class IDW:
    '''
    Inverse distance weighting class
    - Standard IDW
    - Detrended IDW
    '''
    def __init__(self, mx, my, GridX, GridY, mz=None, GridZ=None, power=2, zeroVal=-1):
        
        """
        Args:
            mx: x locations for the points
            my: y locations for the points
            GridX: x locations in grid to interpolate over
            GridY: y locations in grid to interpolate over
            power: power of the inverse distance weighting
        """
               
        # measurement point locations
        self.mx = mx
        self.my = my
        self.mz = mz
        self.npoints = len(mx)
        
        # grid information
        self.GridX = GridX
        self.GridY = GridY
        self.GridZ = GridZ
        
        # data information
        self.data = None
        self.nan_val = []
        
        # IDW parameters
        self.power = power
        self.zeroVal = zeroVal
        
        
        # calculate the distances
        self.calculateDistances()
        
        # calculate the weights
        self.calculateWeights()
        

    def calculateDistances(self):
        '''
        Calculate the distances from the measurement locations to the
        grid locations
        '''
        
        # preallocate
        self.distance = np.empty((self.GridX.shape[0], self.GridX.shape[1], self.npoints))
        
        for i in range(self.npoints):
            self.distance[:,:,i] = np.sqrt((self.GridX - self.mx[i])**2 + (self.GridY - self.my[i])**2)
             
        self.distance[np.where(self.distance == 0)] = np.min(self.distance) # remove any zero values
        

    def calculateWeights(self):
        '''
        Calculate the weights for 
        '''
                
        # calculate the weights
        self.weights = 1/(np.power(self.distance, self.power))
        
        # if there are Inf values, set to 1 as the distance was 0
#         self.weights[np.isinf(self.weights)] = 100
  
        
    def calculateIDW(self, data, local=False):  
        '''
        Calculate the IDW of the data at mx,my over GridX,GridY
        Inputs:
        data    - is the same size at mx,my 
        '''         
        nan_val = ~np.isnan(data)
        w = self.weights[:,:,nan_val]
        data = data[nan_val]
        
#         if local:
#             # apply the modified Sheppards algorthim
#             N = len(data)
#             nq = 13
#             nw = 19
#             nr = np.ceil(np.sqrt(N/3))
#             mx = self.mx[nan_val]
#             my = self.my[nan_val]
#             
#             # Create the Q(x,y) surface for data interpolation
#             # out = sheppard.qshep2(mx, my, d, nq ,nw, lcell, lnext, xmin, ymin, dx, dy, rmax, rsq, a, status, [N,nr])
#             lcell, lnext, xmin, ymin, dx, dy, rmax, rsq, a, status = sheppard.qshep2(self.mx, self.my, \
#                                                                                      data, nq , nw, nr)
#             
# #             IER = ERROR INDICATOR --                                    */
# #     /*           IER = 0 IF NO ERRORS WERE ENCOUNTERED.                */
# #     /*           IER = 1 IF N, NQ, NW, OR NR IS OUT OF RANGE.            */
# #     /*           IER = 2 IF DUPLICATE NODES WERE ENCOUNTERED.            */
# #     /*           IER = 3 IF ALL NODES ARE COLLINEAR.    
#             
#             # the the cell value
#             v = np.zeros(self.GridX.shape)
#             for index,val in np.ndenumerate(v):
#                 v[index] = sheppard.qs2val(self.GridX[index], self.GridY[index], mx, my,\
#                                            data, lcell, lnext, xmin, ymin, dx, dy, rmax, rsq, a)
            
#         else:
        v = np.nansum(w * data, 2) / np.sum(w, 2)
        
        return v 
    

    def detrendedIDW(self, data, flag=0, zeros=None, local=False):
        '''
        Calculate the detrended IDW of the data at mx,my over GridX,GridY
        Inputs:
        data    - is the same size at mx,my 
        '''    
        
        self.detrendData(data, flag, zeros)
        v = self.calculateIDW(self.dtrend, local)
#         vtmp = v.copy()
        v = self.retrendData(v)
        
#         # create a plot for the DOCS
#         fs = 16
#         fw = 'bold'
#         xi = np.array([500, 3000])
#         yi = self.pv[0]*xi + self.pv[1] 
#         fig = plt.figure(figsize=(24,9))        
#          
#         extent = (np.min(self.GridX), np.max(self.GridX), np.min(self.GridY), np.max(self.GridY))
#         # elevational trend
#         ax0 = plt.subplot(1,3,1)
#         plt.plot(self.mz, data, 'o', xi, yi, 'k--')
#         plt.text(2000, 14, 'Slope: %f' % self.pv[0], fontsize=fs, fontweight=fw)
#         plt.xlabel('Elevation [m]', fontsize=fs, fontweight=fw)
#         plt.ylabel('Air Temperature [C]', fontsize=fs, fontweight=fw)              
#          
#         ax1 = plt.subplot(1,3,2)
#         im1 = ax1.imshow(vtmp, aspect='equal',extent=extent)
#         plt.plot(self.mx, self.my, 'o')
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
#         im2 = ax2.imshow(v, aspect='equal',extent=extent)
#         plt.plot(self.mx, self.my, 'o')
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
        
        
        if zeros is not None:
            v[v<0] = 0
        return v
    

    def detrendData(self, data, flag=0, zeros=None):
        '''
        Detrend the data in val using the heights zmeas
        data    - is the same size at mx,my 
        flag     - 1 for positive, -1 for negative, 0 for any trend imposed
        '''
                  
        # calculate the trend on any real data
        nan_val = np.isnan(data)        
        pv = np.polyfit(self.mz[~nan_val], data[~nan_val], 1)
        
        # apply trend constraints
        if flag == 1 and pv[0] < 0:
            pv = np.array([0,0])
        elif (flag == -1 and pv[0] > 0):
            pv = np.array([0,0])
        
        self.pv = pv
        

        
        # detrend the data
        el_trend = self.mz * pv[0] + pv[1]
        
        if zeros is not None:
            data[zeros] = self.zeroVal
        self.dtrend = data - el_trend
        
        
    def retrendData(self, idw):
        '''
        Retrend the IDW values
        '''
        
        # retrend the data
        return idw + self.pv[0]*self.GridZ + self.pv[1]
    
    
    
    
    
    
    

        
        
        
