"""
2016-02-22 Scott Havens

Distributed forcing data over a grid using detrended kriging
"""

import logging

import numpy as np
import pandas as pd

from . import detrended_kriging


class DK:
    """
    Detrended kriging class
    """

    def __init__(self, mx, my, mz, GridX, GridY, GridZ, config):
        """
        Args:
            mx: x locations for the points
            my: y locations for the points
            mz: z locations for the points
            GridX: x locations in grid to interpolate over
            GridY: y locations in grid to interpolate over
            GridZ: z locations in grid to interpolate over
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

        # initialize some things
        self.weights = []
        self.dgrid = []
        self.ad = []

        self.config = config

        # calculate the distances
#         self.calculateDistances()

        # calculate the weights
#         self.calculateWeights()

        self._logger = logging.getLogger(__name__)

    def calculate(self, data):
        """
        Calcluate the deternded kriging for the data and config

        Arg:
            data: numpy array same length as m*
            config: configuration for dk

        Returns:
            v: returns the distributed and calculated value
        """

        nan_val = pd.isnull(data)

        # only calcualte if the stations involved have changed
        # if np.sum(np.array_equal(nan_val,self.nan_val)) != len(self.mx):
        if not np.array_equal(nan_val, self.nan_val):

            self.nan_val = nan_val
            nsta = np.sum(~nan_val)
            self._logger.debug('''Recalculating detrended kriging weights
                                for {} stations ...'''.format(nsta))

            self.calculateWeights()

        # now calculate the trend and the residuals
        self.detrendData(data)

        # distribute the risduals
        r = np.nansum(self.weights * self.residuals, 2)

        # retrend the residuals
        v = self.retrendData(r)

        return v

    def calculateWeights(self):
        """
        Calculate the weights given those stations with nan values for data
        """

        nsta = np.sum(~self.nan_val)
        mx = self.mx[~self.nan_val]
        my = self.my[~self.nan_val]
        mz = self.mz[~self.nan_val]

        # calculate the distances between stations
        ad = np.zeros((nsta, nsta))
        for i in range(nsta):
            ad[i, i] = 0
            for j in range(i+1, nsta):
                ad[i, j] = np.sqrt((mx[i] - mx[j])**2 + (my[i] - my[j])**2)
                ad[j, i] = np.sqrt((mx[i] - mx[j])**2 + (my[i] - my[j])**2)

        self.ad = ad

        # calculate the distances from the grid to the station
        dgrid = np.zeros((self.ngrid, nsta))
        Xa = self.GridX.ravel()
        Ya = self.GridY.ravel()
        for i in range(nsta):
            dgrid[:, i] = np.sqrt((Xa - mx[i])**2 + (Ya - my[i])**2)

        self.dgrid = dgrid

        # calculate the weights
        wg = np.zeros_like(dgrid)
        detrended_kriging.call_grid(self.ad, self.dgrid, mz.astype(np.double),
                                    wg, self.config['dk_ncores'])

        # reshape the weights
        self.weights = np.zeros((self.GridX.shape[0],
                                 self.GridX.shape[1],
                                 nsta))
        for v in range(nsta):
            self.weights[:, :, v] = wg[:, v].reshape(self.GridX.shape)

    def detrendData(self, data):
        """
        Detrend the data in val using the heights zmeas
        data    - is the same size at mx,my
        flag     - 1 for positive, -1 for negative, 0 for any trend imposed
        """

        # calculate the trend on any real data
        pv = np.polyfit(self.mz[~self.nan_val], data[~self.nan_val], 1)

        # apply trend constraints
        if self.config['detrend_slope'] == 1 and pv[0] < 0:
            pv = np.array([0, 0])
        elif (self.config['detrend_slope'] == -1 and pv[0] > 0):
            pv = np.array([0, 0])

        self.pv = pv

        # detrend the data
        el_trend = self.mz[~self.nan_val] * pv[0] + pv[1]

        self.residuals = data[~self.nan_val] - el_trend

    def retrendData(self, r):
        """
        Retrend the residual values
        """

        # retrend the data
        return r + self.pv[0]*self.GridZ + self.pv[1]
