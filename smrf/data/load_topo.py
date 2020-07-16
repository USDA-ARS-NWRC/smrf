
import logging

import numpy as np
from netCDF4 import Dataset
from topocalc import gradient
from topocalc.viewf import viewf
from utm import to_latlon


class Topo():
    """
    Class for topo images and processing those images. Images are:
    - DEM
    - Mask
    - veg type
    - veg height
    - veg k
    - veg tau

    Inputs to topo are the topo section of the config file

    """

    IMAGES = ['dem', 'mask', 'veg_type', 'veg_height', 'veg_k', 'veg_tau']

    def __init__(self, topoConfig):
        self.topoConfig = topoConfig

        self._logger = logging.getLogger(__name__)
        self._logger.info('Reading [TOPO] and making stoporad input')

        self.readNetCDF()

        # calculate the gradient and the sky view factor
        self.gradient()
        self.viewf()

    def readNetCDF(self):
        """
        Read in the images from the config file where the file
        listed is in netcdf format
        """

        # read in the images
        f = Dataset(self.topoConfig['filename'], 'r')

        # netCDF>1.4.0 returns as masked arrays even if no missing values
        # are present. This will ensure that if the array has no missing
        # values, a normal numpy array is returned
        f.set_always_mask(False)

        if 'projection' not in f.variables.keys():
            raise IOError("Topo input files must have projection information")

        self.readImages(f)

        # get some general information about the model domain from the dem
        self.nx = f.dimensions['x'].size
        self.ny = f.dimensions['y'].size

        # create the x,y vectors
        self.x = f.variables['x'][:]
        self.y = f.variables['y'][:]
        [self.X, self.Y] = np.meshgrid(self.x, self.y)

        # There is not a great NetCDF convention on direction for the y-axis.
        # So there is the possibility that the dy will be positive or negative.
        # For the gradient calculations this needs to be absolute spacing.
        self.dx = np.mean(np.diff(self.x))
        self.dy = np.abs(np.mean(np.diff(self.y)))

        # Calculate the center of the basin
        self.cx, self.cy = self.get_center(f, mask_name='mask')

        # Is the modeling domain in the northern hemisphere
        self.northern_hemisphere = self.topoConfig['northern_hemisphere']

        # Assign the UTM zone
        self.zone_number = int(f.variables['projection'].utm_zone_number)

        # Calculate the lat long
        self.basin_lat, self.basin_long = to_latlon(
            self.cx,
            self.cy,
            self.zone_number,
            northern=self.northern_hemisphere)

        self._logger.info('Domain center in UTM Zone {:d} = {:0.1f}m, {:0.1f}m'
                          ''.format(self.zone_number, self.cx, self.cy))
        self._logger.info('Domain center as Latitude/Longitude = {:0.5f}, '
                          '{:0.5f}'.format(self.basin_lat, self.basin_long))

        f.close()

    def readImages(self, f):
        """Read images from the netcdf and set as attributes in the Topo class

        Args:
            f: netcdf dataset object
        """

        # netCDF files are stored typically as 32-bit float, so convert
        # to double or int
        for v_smrf in self.IMAGES:

            if v_smrf in f.variables.keys():
                if v_smrf == 'veg_type':
                    result = f.variables[v_smrf][:].astype(int)
                else:
                    result = f.variables[v_smrf][:].astype(np.float64)

            setattr(self, v_smrf, result)

    def get_center(self, ds, mask_name=None):
        '''
        Function returns the basin center in the native coordinates of the
        a netcdf object.

        The incoming data set must contain at least and x, y and optionally
        whatever mask name the user would like to use for calculating .
        If no mask name is provided then the entire domain is used.

        Args:
            ds: netCDF4.Dataset object containing at least x,y, optionally
                    a mask variable name
            mask_name: variable name in the dataset that is a mask where 1 is
                    in the mask
        Returns:
            tuple: x,y of the data center in the datas native coordinates
        '''
        x = ds.variables['x'][:]
        y = ds.variables['y'][:]

        # Calculate the center of the basin
        if mask_name is not None:
            mask_id = np.argwhere(ds.variables[mask_name][:] == 1)

            # Tuple is required for an upcoming deprecation in numpy
            idx = tuple([mask_id[:, 1]])
            idy = tuple([mask_id[:, 0]])

            x = x[idx]
            y = y[idy]

        return x.mean(), y.mean()

    def gradient(self):
        """
        Calculate the gradient and aspect
        """

        func = self.topoConfig['gradient_method']

        # calculate the gradient and aspect
        g, a = getattr(gradient, func)(
            self.dem, self.dx, self.dy, aspect_rad=True)
        self.slope_radians = g

        # following IPW convention for slope as sin(Slope)
        self.sin_slope = np.sin(g)
        self.aspect = a

    def viewf(self):
        """Calculate the sky view factor
        """

        svf, tcf = viewf(
            self.dem,
            self.dx,
            nangles=self.topoConfig['sky_view_factor_angles'],
            sin_slope=self.sin_slope,
            aspect=self.aspect)

        self.sky_view_factor = svf
        self.terrain_config_factor = tcf
