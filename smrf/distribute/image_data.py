"""
20151231 Scott Havens

Base class for storing image data for distributing forcing data
Anything done here will be available to all variables
"""

import pandas as pd
import numpy as np
from smrf.spatial import idw, dk, grid
import logging

class image_data():
    """    
    Base class for storing image data.
    All other classes, i.e. air_temp(), will be a subclass of
    image_data() so that they all have some common methods
    
    Attributes:
        config: configuration section ofr the variable
        'variable': numpy matrix for the variable
        stations: stations to use for the distribution
        metadata: metadata for the stations
        
    
    
    Methods:
    
    
    """
    
    def __init__(self, variable):
        
        self.variable = variable
        setattr(self, variable, None)
        
        self.gridded = False
        
        self._base_logger = logging.getLogger(__name__)
        
        
    def getConfig(self, config):
        """
        Check the configuration that was set by the user.
        
        Checks for standard parameters and assign to the class
        
        Args:
            config: dict from the [variable] section    
            
        Sets:
            config: parsed configuration
            stations: stations to be used for the variable
        
        """
        
        # check for inverse distance weighting
        if 'distribution' in config:
            if config['distribution'] == 'idw':
                if 'detrend' in config:
                    if config['detrend'].lower() == 'true':
                        config['detrend'] = True
                    elif config['detrend'].lower() == 'false':
                        config['detrend'] = False
                    else:
                        raise ValueError('Detrended configuration setting must be either true/false')
                else:
                    config['detrend'] = False
                    
                if 'slope' in config:
                    if int(config['slope']) not in [-1,0,1]:
                        raise ValueError('Slope value for detrending must be in [-1, 0, 1]')
                    else:
                        config['slope'] = int(config['slope'])
                        
                if 'power' in config:
                    if float(config['power']) < 0:
                        raise ValueError('IDW power must be greater than zero')
                    else:
                        config['power'] = float(config['power'])
                else:
                    config['power'] = 2
                        
                if 'zeroValue' in config:
                    config['zeroValue'] = float(config['zeroValue'])
                else:
                    config['zeroValue'] = None
                
            # check of detrended kriging
            elif config['distribution'] == 'dk':
                if 'slope' in config:
                    if int(config['slope']) not in [-1,0,1]:
                        raise ValueError('Slope value for detrending must be in [-1, 0, 1]')
                    else:
                        config['slope'] = int(config['slope'])
                        
                if 'nthreads' in config:
                    config['nthreads'] = int(config['nthreads'])
                else:
                    config['nthreads'] = 1
                    
                if 'dk_nthreads' in config:
                    config['dk_nthreads'] = int(config['dk_nthreads'])
                else:
                    config['dk_nthreads'] = 1
                        
                if 'regression_method' in config:
                    config['regression_method'] = int(config['regression_method'])
                else:
                    config['regression_method'] = 1
                    
            # check of gridded interpolation
            elif config['distribution'] == 'grid':
                self.gridded = True
                if 'slope' in config:
                    if int(config['slope']) not in [-1,0,1]:
                        raise ValueError('Slope value for detrending must be in [-1, 0, 1]')
                    else:
                        config['slope'] = int(config['slope'])
                       
                if 'detrend' in config:
                    if config['detrend'].lower() == 'true':
                        config['detrend'] = True
                    elif config['detrend'].lower() == 'false':
                        config['detrend'] = False
                    else:
                        raise ValueError('Detrended configuration setting must be either true/false')
                else:
                    config['detrend'] = False
                     
                if 'method' in config:
                    config['method'] = config['method'].lower()
                else:
                    config['method'] = 'linear'
                    
                if 'mask' in config:
                    if config['mask'].lower() == 'true':
                        config['mask'] = True
                    elif config['mask'].lower() == 'false':
                        config['mask'] = False
                    else:
                        raise ValueError('Mask configuration setting must be either true/false')
                else:
                    config['mask'] = False 
                        
                    
        self.getStations(config)
        
                    
        self.config = config
    
    
    def getStations(self, config):
        
        # determine the stations that will be used, alphabetical order
        if 'stations' in config:
            stations = config['stations'].split(',')
            stations = map(str.strip, stations)
            stations.sort()
        else:
            stations = None
            
        self.stations = stations
        
    
    def _initialize(self, topo, metadata):
        """
        Initialize the distribution
        - Determine what distribution method to use
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
            
            
        To do:
            - make a single call to the distribution initialization
            - each dist (idw, dk) takes the same inputs and returns the same
        """
        
        # pull out the metadata subset
        if self.stations is not None:
            metadata = metadata.ix[self.stations]
        else:
            self.stations = metadata.index.values
        self.metadata = metadata
        
        mx = metadata.X.values
        my = metadata.Y.values
        mz = metadata.elevation.values
        
        if self.config['distribution'] == 'idw':
            # inverse distance weighting
            self.idw = idw.IDW(mx, my, topo.X, topo.Y, mz=mz, GridZ=topo.dem, power=self.config['power'])            
        
        elif self.config['distribution'] == 'dk':
            # detrended kriging
            self.dk = dk.DK(mx, my, mz, topo.X, topo.Y, topo.dem, self.config)
            
        elif self.config['distribution'] == 'grid':
            # linear interpolation between points
            self.grid = grid.GRID(self.config, mx, my, topo.X, topo.Y, mz=mz, GridZ=topo.dem, mask=topo.mask)
        
        else:
            raise Exception('Could not determine the distribution method for %s' % self.variable)
    


    def _distribute(self, data, other_attribute=None, zeros=None):
        """
        Distribute the data using the defined distribution method
        
        Args:
            data: dataframe for a single time step
            other_attribute: defult the matrix goes into self.variable
                but this specifies another attribute in self
            zeros: data values that should be treated as zeros
        """
        
        
        # get the data for the desired stations
        # this will also order it correctly how air_temp was initialized
        data = data[self.stations]
        
        if np.sum(data.isnull()) == data.shape[0]:
            raise Exception('%s: All data values are NaN' % self.variable)
        
        
        if self.config['distribution'] == 'idw':
            
            if self.config['detrend']:
                v = self.idw.detrendedIDW(data.values, self.config['slope'], zeros=zeros)
            else:
                v = self.idw.calculateIDW(data.values)
                
        elif self.config['distribution'] == 'dk':
            v = self.dk.calculate(data.values)
        
        elif self.config['distribution'] == 'grid':
            if self.config['detrend']:
                v = self.grid.detrendedInterpolation(data.values, self.config['slope'], self.config['method'])
            else:
                v = self.grid.calculateInterpolation(data.values, self.config['method'])
        
        if other_attribute is not None:
            setattr(self, other_attribute, v)
        else:
            setattr(self, self.variable, v)
            
            
            
#     def distribute_thread(self, queue, *args, **kwargs):
#         """
#         Distribute the data using threading and queue
#         
#         Args:
#             queue: queue dict for all variables
#             data: pandas dataframe for all data required
#         
#         Output:
#             Changes the queue air_temp for the given date
#         """
#         
#         for t in data.index:
#             
#             self.distribute(data.ix[t])
#         
#             queue[self.variable].put( [t, getattr(self, self.variable)] )        
            
            
            