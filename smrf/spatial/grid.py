'''
2016-03-07 Scott Havens

Distributed forcing data over a grid using interpolation
'''

import numpy as np
from scipy.interpolate import griddata


class GRID:
    '''
    Inverse distance weighting class
    - Standard IDW
    - Detrended IDW
    '''
    def __init__(self, config, mx, my, GridX, GridY, mz=None, GridZ=None, mask=None, metadata=None):

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

        self.metadata = metadata
        
        # local elevation gradient
        # if config['grid_local']:

        # mask
        self.mask = np.zeros_like(self.mx, dtype=bool)
        if config['mask']:

            assert(mask.shape == GridX.shape)
            mask = mask.astype(bool)

            x = GridX[0, :]
            y = GridY[:, 0]
            for i, v in enumerate(mx):
                xi = np.argmin(np.abs(x - mx[i]))
                yi = np.argmin(np.abs(y - my[i]))

                self.mask[i] = mask[yi, xi]
        else:
            self.mask = np.ones_like(self.mx, dtype=bool)

    def detrendedInterpolation(self, data, flag=0, grid_method='linear'):
        """
        Interpolate using a detrended approach

        Args:
            data: data to interpolate
            grid_method: scipy.interpolate.griddata interpolation method
        """

        # get the trend, ensure it's positive
        if self.config['grid_local']:
            rtrend = self.detrendedInterpolationLocal(data, flag, grid_method)
        else:
            rtrend = self.detrendedInterpolationMask(data, flag, grid_method)

        return rtrend

    def detrendedInterpolationLocal(self, data, flag=0, grid_method='linear'):
        """
        Interpolate using a detrended approach

        Args:
            data: data to interpolate
            grid_method: scipy.interpolate.griddata interpolation method
        """

        # copy the metadata to append the slope/intercept and data to
        pv = metadata.copy()
        pv['slope'] = np.nan
        pv['intercept'] = np.nan
        pv['data'] = data

        for grid_name,drow in dist_df.iterrows():

            elev = pv.loc[drow].elevation
            pp = np.polyfit(elev, datr[drow], 1)
            if pp[0] < 0:
                pp = np.array([0, 0])
            pv.loc[grid_name, ['slope', 'intercept']] = pp

        # interpolate the slope/intercept
        grid_slope = griddata((pv.utm_x, pv.utm_y), pv.slope, (GridX, GridY), method='cubic')
        grid_intercept = griddata((pv.utm_x, pv.utm_y), pv.intercept, (GridX, GridY), method='cubic')

        # remove the elevation trend from the HRRR precip
        el_trend = pv.elevation * pv.slope + pv.intercept
        dtrend = pv.data - el_trend

        # interpolate the residuals over the DEM
        idtrend = griddata((pv.utm_x, pv.utm_y), dtrend, (GridX, GridY), method='cubic')

        # reinterpolate
        rtrend = idtrend + grid_slope * GridZ + grid_intercept
        
        return rtrend


    def detrendedInterpolationMask(self, data, flag=0, grid_method='linear'):
        """
        Interpolate using a detrended approach

        Args:
            data: data to interpolate
            grid_method: scipy.interpolate.griddata interpolation method
        """

        # get the trend, ensure it's positive
        pv = np.polyfit(self.mz[self.mask].astype(float), data[self.mask], 1)

        # apply trend constraints
        if flag == 1 and pv[0] < 0:
            pv = np.array([0, 0])
        elif (flag == -1 and pv[0] > 0):
            pv = np.array([0, 0])

        self.pv = pv

        # detrend the data
        el_trend = self.mz * pv[0] + pv[1]
        dtrend = data - el_trend

        # interpolate over the DEM grid
        idtrend = griddata((self.mx, self.my),
                           dtrend,
                           (self.GridX, self.GridY),
                           method=grid_method)

        # retrend the data
        rtrend = idtrend + pv[0]*self.GridZ + pv[1]

        return rtrend

    def calculateInterpolation(self, data, grid_method='linear'):
        """
        Interpolate over the grid

        Args:
            data: data to interpolate
            mx: x locations for the points
            my: y locations for the points
            X: x locations in grid to interpolate over
            Y: y locations in grid to interpolate over
        """

        g = griddata((self.mx, self.my),
                     data,
                     (self.GridX, self.GridY),
                     method=grid_method)

        return g
