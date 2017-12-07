
import numpy as np
import pandas as pd
from pykrige.ok import OrdinaryKriging
import matplotlib.pyplot as plt

class KRIGE:
    '''
    Kriging class based on the pykrige package
    '''

    def __init__(self, mx, my, mz, GridX, GridY, GridZ, config):

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
        self.nsta = len(mx)

        # grid information
        self.GridX = GridX
        self.GridY = GridY
        self.GridZ = GridZ
        self.ngrid = GridX.shape[0] * GridX.shape[1]

        # data information
        self.data = None
        self.nan_val = []

        self.config = config

        # kriging parameters for pykrige
        self.variogram_model = 'linear'
        self.variogram_parameters = None
        self.variogram_function = None
        self.nlags = 6
        self.weight = False
        self.anisotropy_scaling = 1.0
        self.anisotropy_angle = 0.0
        self.verbose = False
        self.enable_plotting = False
        self.enable_statistics = False
        self.coordinates_type = 'euclidean' # not in the pypi release of PyKrige
        
        # pykrige execution
        self.backend = 'vectorized'
        self.n_closest_points = None

    def calculate(self, data):
        """
        Estimate the variogram, calculate the model, then apply to the grid

        Arg:
            data: numpy array same length as m*
            config: configuration for dk

        Returns:
            v: Z-values of specified grid or at thespecified set of points. 
               If style was specified as 'masked', zvalues will
               be a numpy masked array.
            sigmasq: Variance at specified grid points or
                     at the specified set of points. If style was specified as 'masked', sigmasq
                     will be a numpy masked array.
        """

        nan_val = pd.isnull(data)
        
        if self.config['detrend']:
            d = self.detrendData(data)
        else:
            d = data.copy()
            
        OK = OrdinaryKriging(self.mx[~nan_val], 
                             self.my[~nan_val], 
                             d[~nan_val], 
                             variogram_model=self.variogram_model,
                             variogram_parameters=self.variogram_parameters,
                             variogram_function=self.variogram_function,
                             nlags=self.nlags,
                             weight=self.weight,
                             anisotropy_scaling=self.anisotropy_scaling,
                             anisotropy_angle=self.anisotropy_angle,
                             verbose=self.verbose,
                             enable_plotting=self.enable_plotting,
                             enable_statistics=self.enable_statistics)
        
        v, ss1 = OK.execute('grid',
                            self.GridX[0,:],
                            self.GridY[:,0],
                            backend=self.backend,
                            n_closest_points=self.n_closest_points)


        if self.config['detrend']:
            # retrend the residuals
            v = self.retrendData(v)

           
        return v, ss1


    def calculateDistances(self):
        '''
        Calculate the distances from the measurement locations to the
        grid locations
        '''

        # preallocate
        self.distance = np.empty((self.GridX.shape[0],
                                  self.GridX.shape[1],
                                  self.npoints))

        for i in range(self.npoints):
            self.distance[:, :, i] = np.sqrt((self.GridX - self.mx[i])**2 +
                                             (self.GridY - self.my[i])**2)

        # remove any zero values
        self.distance[np.where(self.distance == 0)] = np.min(self.distance)

    def calculateWeights(self):
        '''
        Calculate the weights for
        '''

        # calculate the weights
        self.weights = 1.0/(np.power(self.distance, self.power))

        # if there are Inf values, set to 1 as the distance was 0
        # self.weights[np.isinf(self.weights)] = 100

    def calculateIDW(self, data, local=False):
        '''
        Calculate the IDW of the data at mx,my over GridX,GridY
        Inputs:
        data    - is the same size at mx,my
        '''
        nan_val = ~np.isnan(data)
        w = self.weights[:, :, nan_val]
        data = data[nan_val]

        v = np.nansum(w * data, 2) / np.sum(w, 2)

        return v

    def detrended_kriging(self, data, flag=0, zeros=None, local=False):
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
            v[v < 0] = 0
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
            pv = np.array([0, 0])
        elif (flag == -1 and pv[0] > 0):
            pv = np.array([0, 0])

        self.pv = pv

        # detrend the data
        el_trend = self.mz * pv[0] + pv[1]

        if zeros is not None:
            data[zeros] = self.zeroVal
        
        return data - el_trend

    def retrendData(self, idw):
        '''
        Retrend the IDW values
        '''

        # retrend the data
        return idw + self.pv[0]*self.GridZ + self.pv[1]
