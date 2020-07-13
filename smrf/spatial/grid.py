'''
2016-03-07 Scott Havens

Distributed forcing data over a grid using interpolation
'''

import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.interpolate.interpnd import _ndim_coords_from_arrays
from scipy.spatial import qhull as qhull

from smrf.utils.utils import grid_interpolate_deconstructed


class GRID:
    '''
    Inverse distance weighting class
    - Standard IDW
    - Detrended IDW
    '''

    def __init__(self, config, mx, my, GridX, GridY,
                 mz=None, GridZ=None, mask=None, metadata=None):
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

        # local elevation gradient, precalculte the distance dataframe
        if config['grid_local']:
            k = config['grid_local_n']
            dist_df = pd.DataFrame(index=metadata.index, columns=range(k))
            dist_df.index.name = 'cell_id'
            for i, row in metadata.iterrows():

                d = np.sqrt((metadata.latitude - row.latitude) **
                            2 + (metadata.longitude - row.longitude)**2)
                dist_df.loc[row.name] = d.sort_values()[:k].index

            self.dist_df = dist_df

            # stack and reset index
            df = dist_df.stack().reset_index()
            df = df.rename(columns={0: 'cell_local'})
            df.drop('level_1', axis=1, inplace=True)

            # get the elevations
            df['elevation'] = metadata.loc[df.cell_local, 'elevation'].values

            # now we have cell_id, cell_local and elevation for the whole grid
            self.full_df = df

            self.tri = None

        # mask
        self.mask = np.zeros_like(self.mx, dtype=bool)
        if config['grid_mask']:

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

        # take the new full_df and fill a data column
        df = self.full_df.copy()
        df['data'] = data[df['cell_local']].values
        df = df.set_index('cell_id')
        df['fit'] = df.groupby('cell_id').apply(
            lambda x: np.polyfit(x.elevation, x.data, 1))

        # drop all the duplicates
        df.reset_index(inplace=True)
        df.drop_duplicates(subset=['cell_id'], keep='first', inplace=True)
        df.set_index('cell_id', inplace=True)
        df[['slope', 'intercept']] = df.fit.apply(pd.Series)
        # df = df.drop(columns='fit').reset_index()

        # apply trend constraints
        if flag == 1:
            df.loc[df['slope'] < 0, ['slope', 'intercept']] = 0
        elif flag == -1:
            df.loc[df['slope'] > 0, ['slope', 'intercept']] = 0

        # get triangulation
        if self.tri is None:
            xy = _ndim_coords_from_arrays(
                (self.metadata.utm_x, self.metadata.utm_y))
            self.tri = qhull.Delaunay(xy)

        # interpolate the slope/intercept
        grid_slope = grid_interpolate_deconstructed(
            self.tri,
            df.slope.values[:],
            (self.GridX, self.GridY),
            method=grid_method)

        grid_intercept = grid_interpolate_deconstructed(
            self.tri,
            df.intercept.values[:],
            (self.GridX, self.GridY),
            method=grid_method)

        # remove the elevation trend from the HRRR precip
        el_trend = df.elevation * df.slope + df.intercept
        dtrend = df.data - el_trend

        # interpolate the residuals over the DEM
        idtrend = grid_interpolate_deconstructed(
            self.tri,
            dtrend,
            (self.GridX, self.GridY),
            method=grid_method)

        # reinterpolate
        rtrend = idtrend + grid_slope * self.GridZ + grid_intercept

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
