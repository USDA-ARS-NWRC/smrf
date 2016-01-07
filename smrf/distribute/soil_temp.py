"""
20160107 Scott Havens

Distribute soil temperature
This class really doesn't do anything but sets a constant value for the soil temperature
"""

import numpy as np
import logging
from smrf.distribute import image_data

class ts(image_data.image_data):
    """
    ta extends the base class of image_data()
    The ts() class allows for variable specific distributions that 
    go beyond the base class
    
    Attributes:
    
    """
    
    variable = 'soil_temp'
    
    def __init__(self, soilConfig, tempDir=None):
        """
        Initialize ts()
        
        Args:
            solarConfig: configuration from [solar] section
            albedoConfig: configuration from [albedo] section
            stoporad_in: file path to the stoporad_in file created from topo()
            tempDir: location of temp/working directory
        """
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        self.config = soilConfig
                
        self._logger.debug('Initialized distribute.soil_temp')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
            
        """
        
#         self._initialize(topo, metadata)
        self.soil_temp = float(self.config['temp']) * np.ones(topo.dem.shape)
            
    
    def distribute(self):
        """
        Distribute soil temp
        
        Args:
        """
    
#         self._logger.debug('Distributing soil temp')
        pass
        
            
            
    
    