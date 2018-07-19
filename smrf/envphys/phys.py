"""
Created April 15, 2015

Collection of functions to calculate various physical parameters

@author: Scott Havens
"""

import numpy as np
from smrf.envphys import thermal_radiation

def idewpt(vp):
    """
    Calculate the dew point given the vapor pressure

    Args:
        vp - array of vapor pressure values in [Pa]

    Returns:
        dewpt - array same size as vp of the calculated
            dew point temperature [C] (see Dingman 2002).

    """

    # ensure that vp is a numpy array
    vp = np.array(vp)

    # take the log and convert to kPa
    vp = np.log(vp/float(1000))

    # calculate the vapor pressure
    Td = (vp + 0.4926) / (0.0708 - 0.00421*vp)

    return Td

def rh2vp(ta, rh):
    """
    Calculate the vapor pressure given the air temperature
    and relative humidity
    
    Args:
        ta: array of air temperature in [C]
        rh: array of relative humidity from 0-100 [%]
        
    Returns:
        vapor pressure
    """
    
    if rh.flat[0] >= 1.0:
        rh = rh/100.0
        
    satvp = thermal_radiation.sati(ta + 273.15)
    
    return satvp * rh

def satvp(dpt):
    """
    Calculate the saturation vapor pressure at the dew point
    temperature.
    
    Args:
        dwpt: array of dew point temperature in [C]
        
    Returns
       vapor_pressure
    """
    
    return thermal_radiation.sati(dpt + 273.15)
    