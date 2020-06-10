import numpy as np
import pandas as pd
from pykrige.ok import OrdinaryKriging


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

        # Measurement point locations
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
        self.variogram_model = self.config['krig_variogram_model']  # 'linear'
        self.variogram_parameters = None
        self.variogram_function = None
        # np.min([np.round(len(mx)/2), 6])
        self.nlags = self.config['krig_nlags']
        self.weight = self.config['krig_weight']
        self.anisotropy_scaling = self.config['krig_anisotropy_scaling']  # 1.0
        self.anisotropy_angle = self.config['krig_anisotropy_angle']  # 0.0
        self.verbose = False
        self.enable_plotting = False
        self.enable_statistics = False
        # not in the pypi release of PyKrige
        self.coordinates_type = self.config['krig_coordinates_type']

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
                     at the specified set of points. If style was specified as
                     'masked', sigmasq will be a numpy masked array.
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
                            self.GridX[0, :],
                            self.GridY[:, 0],
                            backend=self.backend,
                            n_closest_points=self.n_closest_points)

        if self.config['detrend']:
            # retrend the residuals
            v = self.retrendData(v)

        return v, ss1

    def detrendData(self, data, flag=0, zeros=None):
        '''
        Detrend the data in val using the heights zmeas

        Args:
            data: is the same size at mx,my
            flag: - 1 for positive, -1 for negative, 0 for any trend imposed

        Returns:
            data minus the elevation trend

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
