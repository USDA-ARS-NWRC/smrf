
from spatialnc import ipw
import numpy as np
from netCDF4 import Dataset
import subprocess as sp
from multiprocessing import Process
import os
import logging


class topo():
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

    images = ['dem', 'mask', 'veg_type', 'veg_height', 'veg_k', 'veg_tau']

    def __init__(self, topoConfig, calcInput=True, tempDir=None):
        self.topoConfig = topoConfig
        self.threaded = self.topoConfig['threading']

        if (tempDir is None) | (tempDir == 'WORKDIR'):
            tempDir = os.environ['WORKDIR']
        self.tempDir = tempDir

        self._logger = logging.getLogger(__name__)
        self._logger.info('Reading [TOPO] and making stoporad input')

        # read images
        img_type = self.topoConfig['type']
        if img_type == 'ipw':
            # self.readImages()
            raise IOError('IPW topos are deprecated as of SMRF 0.8.0')
        elif img_type == 'netcdf':
            self.readNetCDF()

        # calculate the necessary images for stoporad
        if calcInput:
            self.stoporadInput()
        else:
            self.stoporad_in_file = None

    def readImages(self):
        """
        Read in the images from the config file
        """
        if 'dem' not in self.topoConfig:
            raise ValueError('DEM file not specified')

        # read in the images
        for v in self.images:
            if v in self.topoConfig:
                i = ipw.IPW(self.topoConfig[v])

                if v == 'veg_type':
                    setattr(self, v, i.bands[0].data.astype(int))
                else:
                    setattr(self, v, i.bands[0].data.astype(np.float64))

                if v == 'dem':
                    # get some general information about the model
                    # domain from the dem
                    self.ny = i.nlines
                    self.nx = i.nsamps
                    self.u = i.bands[0].bline
                    self.v = i.bands[0].bsamp
                    self.du = i.bands[0].dline
                    self.dv = i.bands[0].dsamp
                    self.units = i.bands[0].geounits
                    self.coord_sys_ID = i.bands[0].coord_sys_ID

            else:
                setattr(self, v, None)

        # create the x,y vectors
        self.x = self.v + self.dv*np.arange(self.nx)
        self.y = self.u + self.du*np.arange(self.ny)
        [self.X, self.Y] = np.meshgrid(self.x, self.y)

    def readNetCDF(self):
        """
        Read in the images from the config file where the file
        listed is in netcdf format
        """

        if 'filename' not in self.topoConfig:
            raise ValueError('''Filename was not specified. Please provide
                            a netcdf filename in config file.''')

        # read in the images
        f = Dataset(self.topoConfig['filename'], 'r')

        if 'projection' not in f.variables.keys():
            raise IOError("Topo input files must have projection information")
        # read in the images
        # netCDF files are stored typically as 32-bit float, so convert
        # to double or int
        for v_smrf in self.images:

            # check to see if the user defined any variables e.g. veg_height = veg_length
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

        f.close()

    def stoporadInput(self):
        """
        Calculate the necessary input file for stoporad
        The IPW and WORKDIR environment variables must be set
        """
        if self.topoConfig['type'] != 'ipw':

            f = os.path.abspath(os.path.expanduser(os.path.join(self.tempDir,
                                                                'dem.ipw')))
            i = ipw.IPW()
            i.new_band(self.dem)

            i.add_geo_hdr([self.x[0], self.y[0]],
                          [np.mean(np.diff(self.x)), np.mean(np.diff(self.y))],
                          'm', 'UTM')
            i.write(f, 16)

            self.topoConfig['dem'] = f

        # calculate the skyview
        svfile = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'sky_view.ipw')
        ))
        self._logger.debug('sky view file - %s' % svfile)

        # calculate the gradient
        gfile = os.path.abspath(os.path.expanduser(
            os.path.join(self.tempDir, 'gradient.ipw')
        ))
        self._logger.debug('gradient file - %s' % gfile)

        if self.threaded:

            ts = Process(target=self._viewf, args=(
                self.topoConfig['dem'], svfile))
            ts.start()

            tg = Process(target=self._gradient,
                         args=(self.topoConfig['dem'], gfile))
            tg.start()

            # wait for the processes to stop
            tg.join()
            ts.join()

        else:
            self._viewf(self.topoConfig['dem'], svfile)
            self._gradient(self.topoConfig['dem'], gfile)

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
        self.slope = self.stoporad_in.bands[1].data.astype(np.float64)
        self.aspect = self.stoporad_in.bands[2].data.astype(np.float64)
        self.sky_view = self.stoporad_in.bands[3].data.astype(np.float64)

        # clean up the WORKDIR
        os.remove(gfile)
        os.remove(svfile)

        if self.topoConfig['type'] != 'ipw':
            os.remove(self.topoConfig['dem'])
            self.topoConfig.pop('dem', None)

    def _gradient(self, demFile, gradientFile):
        # calculate the gradient
        cmd = 'gradient %s > %s' % (demFile, gradientFile)
        proc = sp.Popen(cmd, shell=True, env=os.environ.copy()).wait()

        if proc != 0:
            raise OSError('gradient failed')

    def _viewf(self, demFile, viewfFile):
        # calculate the sky view file
        cmd = 'viewf %s > %s' % (demFile, viewfFile)
        proc = sp.Popen(cmd, shell=True, env=os.environ.copy()).wait()

        if proc != 0:
            raise OSError('viewf failed')
