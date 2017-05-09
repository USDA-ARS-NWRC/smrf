'''
The module contains various physics calculations needed for estimating 
the thermal radition and associated values.

Created on May 9, 2017

@author: Scott Havens
'''

__version__ = '0.2.0'

import numpy as np
import subprocess as sp
import math
import os
import datetime
import logging
import pytz


on_rtd = os.environ.get('READTHEDOCS') == 'True'
if on_rtd:
    IPW = '.' # placehold while building the docs
elif 'IPW' not in os.environ:
    IPW = '/usr/local/bin'
else:
    IPW = os.environ['IPW']     # IPW executables


# define some constants
MAXV = 1.0              # vis albedo when gsize = 0
MAXIR = 0.85447         # IR albedo when gsize = 0
IRFAC = -0.02123        # IR decay factor
VFAC = 500.0            # visible decay factor
VZRG = 1.375e-3         # vis zenith increase range factor
IRZRG = 2.0e-3          # ir zenith increase range factor
IRZ0 = 0.1              # ir zenith increase range, gsize=0
STEF_BOLTZ = 5.6697e-8  # stephman boltzman constant
EMISS_TERRAIN = 0.98    # emissivity of the terrain
EMISS_VEG = 0.96        # emissivity of the vegitation
FREEZE = 273.16         # freezing temp K
BOIL = 373.15           # boiling temperature K
STD_LAPSE_M = -0.0065   # lapse rate (K/m)
STD_LAPSE = -6.5        # lapse rate (K/km)
SEA_LEVEL = 1.013246e5  # sea level pressure
RGAS = 8.31432e3        # gas constant (J / kmole / deg)
GRAVITY = 9.80665       # gravity (m/s^2)
MOL_AIR = 28.9644       # molecular weight of air (kg / kmole)

    
    
def thermal_correct_terrain(th, ta, viewf):
    '''
    Correct the thermal radiation for terrain assuming that
    the terrain is at the air temperature and the pixel and 
    a sky view
    
    Inputs:
    th - thermal radiation
    ta - air temperature [C]
    viewf - sky view factor from view_f
    
    Outputs:
    th_c - correct thermal radiation
    
    20150611 Scott Havens
    '''
    
    # thermal emitted from the terrain
    terrain = STEF_BOLTZ * EMISS_TERRAIN * np.power(ta + 273.15, 4)
    
    # correct the incoming thermal
    return viewf * th + (1 - viewf) * terrain
    
    
def thermal_correct_canopy(th, ta, tau, veg_height, height_thresh=2):
    '''
    Correct thermal radiation for vegitation.  It will only correct
    for pixels where the veg height is above a threshold. This ensures
    that the open areas don't get this applied.  Vegitation temp
    is assumed to be at air temperature
    
    Inputs:
    th - thermal radiation
    ta - air temperature [C]
    tau - transmissivity of the canopy
    veg_height - vegitation height for each pixel
    height_thresh - threshold hold for height to say that there is veg in the pixel
    
    Output:
    th_c - corrected thermal radiation
    
    Equations from Links and Marks 1999
    20150611 Scott Havens
    '''
    
    # thermal emitted from the canopy
    veg = STEF_BOLTZ * EMISS_VEG * np.power(ta + 273.15, 4)
    
    # pixels with canopy above the threshold
    ind = veg_height > height_thresh
    
    # correct incoming thermal
    th[ind] = tau[ind] * th[ind] + (1 - tau[ind]) * veg[ind]
    
    return th


def precipitable_water(ta, ea):
    """
    Estimate the precipitable water from Prata (1996) :cite:`Prata:1996`
    """
    return 4650*ea/ta


def Dilly1998(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Dilly & O'Brian (1998)
    :cite:`Dilly&OBrian:1998` using the equation:
    
    .. math::
        L_{clear} = 59.38 + 113.7 * \frac{T_a}{273.16}^6 + 96.96 \sqrt{w/25}
            
    Where :math:`T_a` is the air temperature and :math:`w` is the amount of 
    precipitable water. The preipitable water is estimated as :math:`4650 e_o/T_o`
    from Prata (1996) :cite:`Prata:1996`.
    
    Args:
        ta - distributed air temperature [degree C]
        ea - distrubted vapor pressure [kPa]
        
    Returns:
        th - clear sky long wave radiation [W/m2]
    
    20170509 Scott Havens
    """
    
    ta = ta + 273.16                    # convert to K
    w = precipitable_water(ta, ea)  # precipitable water
    
    th = 59.38 + 113.7 * (ta/273.16)**6 + 96.96*np.sqrt(w/25)
    
    return th


def calc_long_wave(e, ta):
    """
    Apply the Stephan-Boltzman equation for longwave
    """
    return e * STEF_BOLTZ * ta**4

def Prata1996(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Prata (1996)
    :cite:`Prata:1996` using the equation:
    
    .. math::
        \epsilon_{clear} = 1 - (1 + w) exp(-1.2 + 3w)^(1/2)
        
    Where :math:`w` is the amount of precipitable water. The preipitable 
    water is estimated as :math:`4650 e_o/T_o` from Prata (1996) :cite:`Prata:1996`.
    
    Args:
        ta - distributed air temperature [degree C]
        ea - distrubted vapor pressure [kPa]
        
    Returns:
        th - clear sky long wave radiation [W/m2]
    
    20170509 Scott Havens
    """
    
    ta = ta + 273.16                    # convert to K
    w = precipitable_water(ta, ea)  # precipitable water
    
    # clear sky emmissivity
    ec = 1 - (1 + w) * np.exp(-np.sqrt(1.2 + 3*w))
    
    return calc_long_wave(ec, ta)


def Angstrom1918(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Prata (1996)
    :cite:`Prata:1996` using the equation:
    
    .. math::
        \epsilon_{clear} = 0.83 - 0.18 * 10^{-0.067 e_a}
        
    Where :math:`e_a` is the vapor pressure.
    
    Args:
    ta - distributed air temperature [degree C]
        ea - distrubted vapor pressure [kPa]
        
    Returns:
        th - clear sky long wave radiation [W/m2]
    
    20170509 Scott Havens
    """
    
    ta = ta + 273.16                    # convert to K
    e = 0.83 - 0.18 * np.power(10, -0.067*ea)
    
    return calc_long_wave(e, ta)

 
def hysat(pb, tb, L, h, g, m):        
    '''
    integral of hydrostatic equation over layer with linear temperature variation
    
        pb = base level pressure
        tb = base level temp (K)
        L  = lapse rate (deg/km)
        h  = layer thickness (km)
        g  = grav accel (m/s^2)
        m  = molec wt (kg/kmole)
    
     (the factors 1.e-3 and 1.e3 are for units conversion)
     20151027 Scott Havens
     '''
    
    if L == 0:
        return pb * np.exp(-g * m * h * 1.e3/(RGAS * tb))
    else:
        return pb * np.power(tb/(tb + L * h), g * m/(RGAS * L * 1.e-3))
       

def satw(tk):
    '''
    Saturation vapor pressure of water. from IPW satw
    20151027 Scott Havens
    '''
    
    # remove bad values
    tk[tk < 0] = np.nan

    l10 = np.log(10.0)

    btk = BOIL/tk
    x = -7.90298*(btk- 1.0) + 5.02808*np.log(btk)/l10 - \
            1.3816e-7*(np.power(10.0,1.1344e1*(1.0 - tk/BOIL))-1.) + \
            8.1328e-3*(np.power(10.0,-3.49149*(btk - 1.0)) - 1.0) + \
            np.log(SEA_LEVEL)/l10;

    x = np.power(10.0,x);

    return x


def sati(tk):
    '''
    saturation vapor pressure over ice. From IPW sati
    20151027 Scott Havens
    '''
    
    # remove bad values
    tk[tk < 0] = np.nan
    
    # preallocate
    x = np.empty(tk.shape)
    
    # vapor above freezing
    ind = tk > FREEZE
    x[ind] = satw(tk[ind])
    
    # vapor below freezing
    l10 = np.log(10.0)
    x[~ind] = 100.0 * np.power(10.0, -9.09718*((FREEZE/tk[~ind]) - 1.0) - 3.56654*np.log(FREEZE/tk[~ind])/l10 + \
            8.76793e-1*(1.0 - (tk[~ind]/FREEZE)) + np.log(6.1071)/l10)


    return x


def brutsaert(ta, l, ea, z, pa):
    '''
    Calculate atmosphere emissivity
    
    ta - air temp (K)
    l - temperature lapse rate (deg/m)
    ea - vapor pressure (Pa)
    z - elevation (z)
    pa - air pressure (Pa)
    
    20151027 Scott Havens
    '''
    
    t_prime = ta - (l * z)
    rh = ea / sati(ta)
    rh[rh > 1] = 1
    
    e_prime = (rh * sati(t_prime))/100.0

    air_emiss = (1.24*np.power(e_prime/t_prime, 1./7.0))*pa/SEA_LEVEL

    air_emiss[air_emiss > 1.0] = 1.0

    return air_emiss
    


def topotherm(ta, tw, z, skvfac):
    '''
    Calculate the clear sky thermal radiation.  topotherm calculates  thermal 
    radiation from the atmosphere corrected for topographic effects, from near 
    surface air temperature Ta, dew point temperature DPT, and elevation.  Based 
    on a model by Marks and Dozier (1979).
    
    20151027 Scott Havens
    '''
    
    # convert ta and tw from C to K
    ta = ta + FREEZE;
    tw = tw + FREEZE;

    # if below zero set to nan
    tw[tw < 0] = np.nan
    ta[ta < 0] = np.nan

    # calculate theoretical sea level
    # atmospheric emissivity
    # from reference level ta, tw, and z
    ind = tw > ta
    tw[ind] = ta[ind]
    
    ea = sati(tw)
    emiss = brutsaert(ta, STD_LAPSE_M, ea, z, SEA_LEVEL)

    # calculate sea level air temp
    T0 = ta - (z * STD_LAPSE_M);

    # adjust emiss for elev, terrain
    # veg, and cloud shading
    press = hysat(SEA_LEVEL, T0, STD_LAPSE, z/1000.0, GRAVITY, MOL_AIR)

    # elevation correction
    emiss *= press/SEA_LEVEL

    # terrain factor correction
    emiss = (emiss * skvfac) + (1.0 - skvfac)

    # check for emissivity > 1.0
    emiss[emiss > 1.0] = 1.0

    # calculate incoming lw rad
    return emiss * STEF_BOLTZ * np.power(ta, 4)





