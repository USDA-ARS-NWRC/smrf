"""
20160106 Scott Havens

Distribute albedo

"""

import numpy as np
import logging
from smrf.distribute import image_data
from smrf.envphys import radiation
import smrf.utils as utils
import matplotlib.pyplot as plt

class albedo(image_data.image_data):
    """
    ta extends the base class of image_data()
    The albedo() class allows for variable specific distributions that 
    go beyond the base class
    
    Attributes:
        config: configuration from [albedo] section
        albedo_vis: numpy matrix of the visible albedo
        albedo_ir: numpy matrix of the ir albedo
        stations: stations to be used in alphabetical order
    
    """
    
    variable = 'albedo'
    min = 0
    max = 1
    
    def __init__(self, albedoConfig):
        """
        Initialize albedo()
        
        Args:
            albedoConfig: configuration from [albedo] section
        """
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
        # check and assign the configuration        
        if 'grain_size' not in albedoConfig:
            albedoConfig['grain_size'] = 300
        else:
            albedoConfig['grain_size'] = float(albedoConfig['grain_size'])
        
        if 'max_grain' not in albedoConfig:
            albedoConfig['max_grain'] = 2000
        else:
            albedoConfig['max_grain'] = float(albedoConfig['max_grain'])
            
        if 'dirt' not in albedoConfig:
            albedoConfig['dirt'] = 2.0
        else:
            albedoConfig['dirt'] = float(albedoConfig['dirt'])
            
        self.config = albedoConfig
                
        self._logger.debug('Initialized distribute.albedo')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls image_data.image_data._initialize()
        
        Args:
            topo: smrf.data.loadTopo.topo instance contain topo data/info
            metadata: metadata dataframe containing the station metadata
                        
        """
        
#         self._initialize(topo, metadata)
                  
            
        
    def distribute(self, current_time_step, cosz, storm_day):
        """
        Distribute albedo
        
        Args:
            current_time_step: Current time step in datetime object
            storm_day: numpy matrix of the decimal days since it last
                snowed at a grid cell
            
        """
    
        self._logger.debug('Distributing albedo')
        
        # only need to calculate albedo if the sun is up
        if cosz is not None:
                   
            alb_v, alb_ir = radiation.albedo(storm_day, cosz, 
                                             self.config['grain_size'], 
                                             self.config['max_grain'], 
                                             self.config['dirt'])
            
            self.albedo_vis = alb_v
            self.albedo_ir = alb_ir  
    
        else:
            self.albedo_vis = np.zeros(storm_day.shape)
            self.albedo_ir = np.zeros(storm_day.shape)
            
            
            
            
            
            
            
            
            
    
    