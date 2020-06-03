
import logging
import os
import subprocess as sp

import numpy as np
from netCDF4 import Dataset
from spatialnc import ipw
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
    topo will guess the location of the WORKDIR env variable
    and should work for unix systems.

    Attributes:
        topoConfig: configuration for topo
        tempDir: location of temporary working directory
        dem: numpy array for the DEM
        mask: numpy array for the mask
        veg_type: numpy array for the veg type
        veg_height: numpy array for the veg height
        veg_k: numpy array for the veg K
        veg_tau: numpy array for the veg transmissivity
        sky_view:
        ny: number of columns in DEM
        nx: number of rows in DEM
        u,v: location of upper left corner
        du, dv: step size of grid
        unit: geo header units of grid
        coord_sys_ID: coordinate syste,
        x,y: position vectors
        X,Y: position grid
        stoporad_in: numpy array for the sky view factor

    """

    IMAGES = ['dem', 'mask', 'veg_type', 'veg_height', 'veg_k', 'veg_tau']

    def __init__(self, topoConfig, tempDir=None):
        self.topoConfig = topoConfig

        if (tempDir is None) | (tempDir == 'WORKDIR'):
            tempDir = os.environ['WORKDIR']
        self.tempDir = tempDir

        self._logger = logging.getLogger(__name__)
        self._logger.info('Reading [TOPO] and making stoporad input')

        self.readNetCDF()

        # calculate the gradient and the sky view factor
        self.gradient()
        self.viewf()

        # create the stoporad.in file
        self.stoporadInput()

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

        # read in the images
        # netCDF files are stored typically as 32-bit float, so convert
        # to double or int
        for v_smrf in self.IMAGES:

            # check to see if the user defined any variables
            # e.g. veg_height = veg_length
            if v_smrf in self.topoConfig.keys():
                v_file = self.topoConfig[v_smrf]
            else:
                v_file = v_smrf

            if v_file in f.variables.keys():
                if v_smrf == 'veg_type':
                    result = f.variables[v_file][:].astype(int)
                else:
                    result = f.variables[v_file][:].astype(np.float64)

            setattr(self, v_smrf, result)

        # get some general information about the model domain from the dem
        self.nx = f.dimensions['x'].size
        self.ny = f.dimensions['y'].size

        # create the x,y vectors
        self.x = f.variables['x'][:]
        self.y = f.variables['y'][:]
        [self.X, self.Y] = np.meshgrid(self.x, self.y)

        self.dx = np.mean(np.diff(self.x))
        self.dy = np.mean(np.diff(self.y))

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

        Args:
            gfile: IPW file to write the results to
        """

        func = self.topoConfig['gradient_method']

        # calculate the gradient and aspect
        g, a = getattr(gradient, func)(
            self.dem, self.dx, self.dy, aspect_rad=True)
        self.slope_radians = g
        self.sin_slope = np.sin(g)  # IPW stores slope as sin(Slope)
        self.aspect = a

    def viewf(self):
        """Calculate the sky view factor
        """

        svf, tcf = viewf(self.dem, self.dx, nangles=72,
                         sin_slope=self.sin_slope, aspect=self.aspect)

        self.sky_view_factor = svf
        self.terrain_config_factor = tcf

    def add_geo_hdr(self, image):
        """Add an IPW geoheader to the image

        Arguments:
            image {IPW} -- IPW class
        """

        image.add_geo_hdr(
            [self.x[0], self.y[0]],
            [self.dx, self.dx],
            'm',
            'UTM')

        return image

    def stoporadInput(self):
        """
        Build the stoporad.in file. This will have to write out

        The stoporad.in file is a 5 band image with the following:
            - dem
            - slope
            - aspect
            - sky view factor
            - terrain factor
        """

        # DEM ipw image
        dem_file = os.path.join(self.tempDir, 'dem.ipw')
        i = ipw.IPW()
        i.new_band(self.dem)
        i = self.add_geo_hdr(i)
        i.write(dem_file, 16)

        # slope
        slope_file = os.path.join(self.tempDir, 'slope.ipw')

        i = ipw.IPW()
        i.new_band(self.sin_slope)
        i = self.add_geo_hdr(i)
        i.write(slope_file, 8)

        # aspect
        aspect_file = os.path.join(self.tempDir, 'aspect.ipw')
        i = ipw.IPW()
        i.new_band(self.aspect)
        i = self.add_geo_hdr(i)
        i.bands[0].units = 'radians'
        i.write(aspect_file, 8)

        # modify the LQ headers
        # will only use the max/min floats for the LQ hearder, however
        # the shade function checks the lq header max and will error
        # with these slopes
        slope_file2 = os.path.join(self.tempDir, 'slope2.ipw')
        cmd = 'requant -m 0,1 {} > {}'.format(slope_file, slope_file2)
        proc = sp.Popen(cmd, shell=True, env=os.environ.copy()).wait()
        if proc != 0:
            raise OSError('slope LQ header modification failed')

        # calculate the view factor
        svf_file = os.path.join(self.tempDir, 'sky_view.ipw')
        i = ipw.IPW()
        i.new_band(self.sky_view_factor)
        i.new_band(self.terrain_config_factor)
        i = self.add_geo_hdr(i)
        i.bands[0].units = 'radians'
        i.write(svf_file, 8)

        # combine into a value
        stoporad_file = os.path.join(self.tempDir, 'stoporad_in.ipw')

        cmd = f"mux {dem_file} {slope_file2} {aspect_file} " \
            f"{svf_file} > {stoporad_file}"
        proc = sp.Popen(cmd, shell=True).wait()

        if proc != 0:
            raise OSError('mux for stoporad_in.ipw failed')

        self.stoporad_in_file = stoporad_file

        # clean up the WORKDIR
        # os.remove(dem_file) # This may be able to be removed after shade is implemented
        os.remove(svf_file)
        os.remove(slope_file)
        os.remove(slope_file2)
        os.remove(aspect_file)
