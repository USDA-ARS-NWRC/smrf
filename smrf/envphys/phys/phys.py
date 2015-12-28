'''
Created April 15, 2015

Collection of functions to calculate various physical parameters

@author: Scott Havens
'''


import numpy as np


def idewpt(vp):
    '''
    Calculate the dew point given the vapor pressure
    
    Args:
    vp - array of vapor pressure values in [Pa]
    
    Out:
    dewpt - array same size as vp of the calculated
        dew point temperature [C]
        
    (see Dingman 2002)
        
    '''
    
    # ensure that vp is a numpy array
    vp = np.array(vp)
    
    # take the log and convert to kPa
    vp = np.log(vp/float(1000))    
    
    # calculate the vapor pressure
    Td = (vp + 0.4926) / (0.0708 - 0.00421*vp)
   
    return Td

