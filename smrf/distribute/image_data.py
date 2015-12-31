"""
20151231 Scott Havens

Base class for storing image data for distributing forcing data
"""

import pandas as pd
import numpy as np
import logging

class image_data():
    """
    Base class for storing image data.
    All other classes, i.e. air_temp(), will be a subclass of
    image_data() so that they all have some common methods
    
    Attributes:
        images: Pandas panel for storing the 3D image data
    
    
    Methods:
    
    
    """
    
    def __init__(self, variable):
        
        self.variable = variable
        self.images = None
        
        self._base_logger = logging.getLogger(__name__)
    
    def method(self):
        
        pass
        
        