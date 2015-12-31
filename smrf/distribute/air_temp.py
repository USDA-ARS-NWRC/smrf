"""
20151230 Scott Havens

Distribute air temperature

"""

import numpy as np
import logging
from smrf.spatial import idw
from smrf.distribute import image_data
import matplotlib.pyplot as plt

class ta(image_data.image_data):
    """
    ta extends the base class of image_data()
    
    Attributes:
        taConfig: configuration from [air_temp] section
        images: Pandas panel for 3D data
        stations: stations to be used in alphabetical order
    
    """
    
    variable = 'air_temp'
    
    def __init__(self, taConfig):
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        # check the configuration
        if 'detrend' in taConfig:
            if taConfig['detrend'].lower() == 'true':
                taConfig['detrend'] = True
            elif taConfig['detrend'].lower() == 'false':
                taConfig['detrend'] = False
            else:
                raise ValueError('Detrended configuration setting must be either true/false')
        else:
            taConfig['detrend'] = False
            
        if 'slope' in taConfig:
            if int(taConfig['slope']) not in [-1,0,1]:
                raise ValueError('Slope value for detrending must be in [-1, 0, 1]')
            else:
                taConfig['slope'] = int(taConfig['slope'])
                
        self.taConfig = taConfig
         
        
        
        # determine the stations that will be used, alphabetical order
        stations = self.taConfig['stations'].split(',')
        stations = map(str.strip, stations)
        stations.sort()
        self.stations = stations
        
        self._logger.debug('Initialized distribute.air_temp')
        
        
    def initialize(self, topo, metadata):
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
        meta = metadata.ix[self.stations]
        
        if self.taConfig['distribution'] == 'idw':
            
            mx = meta.X.values
            my = meta.Y.values
            mz = meta.elevation.values
            
            self.idw = idw.IDW(mx, my, topo.X, topo.Y, mz=mz, GridZ=topo.dem.bands[0].data, power=2)            
        
        
        else:
            raise Exception('Could not determine the distribution method for air_temp')
        
        
    def distribute(self, data):
        """
        Distribute air temperature
        
        Args:
            data: air_temp data frame
            
        """
    
        # get the data for the desired stations
        # this will also order it correctly how air_temp was initialized
        data = data[self.stations]
        
        
        if self.taConfig['distribution'] == 'idw':
            
            if self.taConfig['detrend']:
                v = self.idw.detrendedIDW(data.values, self.taConfig['slope'])
            else:
                v = self.idw.calculateIDW(data.values)
    
    
    
    
        return v
    
    
    