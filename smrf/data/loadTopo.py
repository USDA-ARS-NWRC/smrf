
import logging
import os
import subprocess as sp

import numpy as np
from netCDF4 import Dataset
from topocalc import gradient
from spatialnc import ipw
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

    def __init__(self, topoConfig, calcInput=True, tempDir=None):
        self.topoConfig = topoConfig

        if (tempDir is None) | (tempDir == 'WORKDIR'):
            tempDir = os.environ['WORKDIR']
        self.tempDir = tempDir

        self._logger = logging.getLogger(__name__)
        self._logger.info('Reading [TOPO] and making stoporad input')

        self.readNetCDF()

        # calculate the necessary images for stoporad
        if calcInput:
            self.stoporadInput()
        else:
            self.stoporad_in_file = None

    # IPW Support has been deprecated since 0.8.0, but it now
    # has been fully removed.

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

    def stoporadInput(self):
        """
        Calculate the necessary input file for stoporad
        The IPW and WORKDIR environment variables must be set
        """
        # if self.topoConfig['type'] != 'ipw':
        #
        f = os.path.abspath(os.path.expanduser(os.path.join(self.tempDir,
                                                            'dem.ipw')))
        i = ipw.IPW()
        i.new_band(self.dem)

        i.add_geo_hdr([self.x[0], self.y[0]],
                      [np.mean(np.diff(self.x)), np.mean(np.diff(self.y))],
                      'm', 'UTM')
        i.write(f, 16)

        self.topoConfig['dem'] = f

        # calculate the gradient
        gfile = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'gradient.ipw')
        ))
        self._logger.debug('gradient file - %s' % gfile)

        self.gradient(gfile)

        # calculate the view factor
        svfile = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'sky_view.ipw')
        ))
        self._logger.debug('sky view file - %s' % svfile)

        self._viewf(self.topoConfig['dem'], svfile)

        # combine into a value
        sfile = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'stoporad_in.ipw')
        ))
        self._logger.debug('stoporad in file - %s' % sfile)

        cmd = 'mux %s %s %s > %s' % (self.topoConfig['dem'],
                                     gfile,
                                     svfile,
                                     sfile)
        proc = sp.Popen(cmd, shell=True).wait()

        if proc != 0:
            raise OSError('mux for stoporad_in.ipw failed')

        # read in the stoporad file to store in memory
        self.stoporad_in = ipw.IPW(sfile)
        self.stoporad_in_file = sfile
        # self.slope = self.stoporad_in.bands[1].data.astype(np.float64)
        # self.aspect = self.stoporad_in.bands[2].data.astype(np.float64)
        self.sky_view = self.stoporad_in.bands[3].data.astype(np.float64)

        # clean up the WORKDIR
        os.remove(gfile)
        os.remove(svfile)

        os.remove(self.topoConfig['dem'])
        self.topoConfig.pop('dem', None)

    def gradient(self, gfile):
        """
        Calculate the gradient and aspect

        Args:
            gfile: IPW file to write the results to
        """

        func = self.topoConfig['gradient_method']
        dx = np.mean(np.diff(self.x))
        dy = np.mean(np.diff(self.x))

        # calculate the gradient and aspect
        g, a = getattr(gradient, func)(self.dem, dx, dy, aspect_rad=True)
        self.slope_radians = g
        self.sin_slope = np.sin(g)  # IPW stores slope as sin(Slope)
        self.aspect = a

        # convert to ipw images for stoporad, the spatialnc package
        # will only use the max/min floats for the LQ hearder, however
        # the shade function checks the lq header max and will error
        # with these slopes
        sfile = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'slope.ipw')
        ))
        i = ipw.IPW()
        i.new_band(self.sin_slope)
        i.add_geo_hdr([self.x[0], self.y[0]],
                      [np.mean(np.diff(self.x)), np.mean(np.diff(self.y))],
                      'm', 'UTM')
        i.write(sfile, 8)

        # aspect
        afile = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'aspect.ipw')
        ))
        i = ipw.IPW()
        i.new_band(a)
        i.add_geo_hdr([self.x[0], self.y[0]],
                      [np.mean(np.diff(self.x)), np.mean(np.diff(self.y))],
                      'm', 'UTM')
        i.bands[0].units = 'radians'
        i.write(afile, 8)

        # modify the LQ headers
        sfile2 = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'slope2.ipw')
        ))
        cmd = 'requant -m 0,1 {} > {}'.format(sfile, sfile2)
        proc = sp.Popen(cmd, shell=True, env=os.environ.copy()).wait()
        if proc != 0:
            raise OSError('slope LQ header modification failed')

        # mux together for gradient
        cmd = 'mux {} {} > {}'.format(sfile2, afile, gfile)
        proc = sp.Popen(cmd, shell=True, env=os.environ.copy()).wait()
        if proc != 0:
            raise OSError('gradient mux failed')

        # clean up
        os.remove(sfile)
        os.remove(sfile2)
        os.remove(afile)

    def _viewf(self, demFile, viewfFile):
        # calculate the sky view file
        cmd = 'viewf %s > %s' % (demFile, viewfFile)
        proc = sp.Popen(cmd, shell=True, env=os.environ.copy()).wait()

        if proc != 0:
            raise OSError('viewf failed')
