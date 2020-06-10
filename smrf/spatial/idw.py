import numpy as np


class IDW:
    '''
    Inverse distance weighting class for distributing input data. Availables
    options are:

    * Standard IDW
    * Detrended IDW

    '''

    def __init__(self, mx, my, GridX, GridY, mz=None, GridZ=None,
                 power=2, zeroVal=-1):
        """
        Args:
            mx: x locations for the points
            my: y locations for the points
            GridX: x locations in grid to interpolate over
            GridY: y locations in grid to interpolate over
            mz: elevation for the points
            GridZ: Elevation values for the points to interpolate over for
                   trended data
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
        self.dtrend = data - el_trend

    def retrendData(self, idw):
        '''
        Retrend the IDW values
        '''

        # retrend the data
        return idw + self.pv[0]*self.GridZ + self.pv[1]
