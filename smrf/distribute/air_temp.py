"""
20151230 Scott Havens

Distribute air temperature

"""

import numpy as np
import logging
from smrf.distribute import image_data
import matplotlib.pyplot as plt

class ta(image_data.image_data):
    """
    ta extends the base class of image_data()
    The ta() class allows for variable specific distributions that 
    go beyond the base class
    
    Attributes:
        config: configuration from [air_temp] section
        air_temp: numpy matrix of the air temperature
        stations: stations to be used in alphabetical order
    
    """
    
    variable = 'air_temp'
    output_variables = ['air_temp'] # these are variables that can be output
    
    def __init__(self, taConfig):
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        # check and assign the configuration
        self.getConfig(taConfig)
        
        self._logger.debug('Initialized distribute.air_temp')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
                        
        """
        
        self._initialize(topo, metadata)
                
        
    def distribute(self, data):
        """
        Distribute air temperature
        
        Args:
            data: air_temp data frame
            
        """
    
        self._logger.debug('Distributing air_temp')
        
        self._distribute(data)
    
    

    
    
    