'''
The module contains various physics calculations needed for estimating 
the thermal radition and associated values.
'''
from smrf.distribute import vapor_pressure

__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2017-05-09"
__version__ = "0.2.0"

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
    
    Args:
        th: thermal radiation
        ta: air temperature [C]
        viewf: sky view factor from view_f
    
    Returns:
        corrected thermal radiation
    
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
    
    Args:
        th: thermal radiation
        ta: air temperature [C]
        tau: transmissivity of the canopy
        veg_height: vegitation height for each pixel
        height_thresh: threshold hold for height to say that there is veg in the pixel
    
    Returns:
        corrected thermal radiation
    
    Equations from Link and Marks 1999 :cite:`Link&Marks:1999`
    
    20150611 Scott Havens
    '''
    
    # thermal emitted from the canopy
    veg = STEF_BOLTZ * EMISS_VEG * np.power(ta + FREEZE, 4)
    
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
    Estimate clear-sky downwelling long wave radiation from Dilley & O'Brian (1998)
    :cite:`Dilley&OBrian:1998` using the equation:
    
    .. math::
        L_{clear} = 59.38 + 113.7 * \\left( \\frac{T_a}{273.16} \\right)^6 + 96.96 \\sqrt{w/25}
            
    Where :math:`T_a` is the air temperature and :math:`w` is the amount of 
    precipitable water. The preipitable water is estimated as :math:`4650 e_o/T_o`
    from Prata (1996) :cite:`Prata:1996`.
    
    Args:
        ta: distributed air temperature [degree C]
        ea: distrubted vapor pressure [kPa]
        
    Returns:
        clear sky long wave radiation [W/m2]
    
    20170509 Scott Havens
    """
    
    ta = ta + FREEZE                    # convert to K
    w = precipitable_water(ta, ea)  # precipitable water
    
    th = 59.38 + 113.7 * (ta/273.16)**6 + 96.96*np.sqrt(w/25)
    
    return th


def calc_long_wave(e, ta):
    """
    Apply the Stephan-Boltzman equation for longwave
    """
    return e * STEF_BOLTZ * np.power(ta, 4)

def Prata1996(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Prata (1996)
    :cite:`Prata:1996` using the equation:
    
    .. math::
        \epsilon_{clear} = 1 - (1 + w) * exp(-1.2 + 3w)^{1/2}
        
    Where :math:`w` is the amount of precipitable water. The preipitable 
    water is estimated as :math:`4650 e_o/T_o` from Prata (1996) :cite:`Prata:1996`.
    
    Args:
        ta: distributed air temperature [degree C]
        ea: distrubted vapor pressure [kPa]
        
    Returns:
        clear sky long wave radiation [W/m2]
    
    20170509 Scott Havens
    """
    
    ta = ta + FREEZE                    # convert to K
    w = precipitable_water(ta, ea)  # precipitable water
    
    # clear sky emmissivity
    ec = 1 - (1 + w) * np.exp(-np.sqrt(1.2 + 3*w))
    
    return calc_long_wave(ec, ta)


def Angstrom1918(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Angstrom (1918) :cite:`Angstrom:1918` 
    as cited by Niemela et al (2001) :cite:`Niemela&al:2001` using the equation:
    
    .. math::
        \\epsilon_{clear} = 0.83 - 0.18 * 10^{-0.067 e_a}
        
    Where :math:`e_a` is the vapor pressure.
    
    Args:
        ta: distributed air temperature [degree C]
        ea: distrubted vapor pressure [kPa]
        
    Returns:
        clear sky long wave radiation [W/m2]
    
    20170509 Scott Havens
    """
    
    ta = ta + FREEZE                  # convert to K
    e = 0.83 - 0.18 * np.power(10, -0.067*ea)
    
    return calc_long_wave(e, ta)

 
def hysat(pb, tb, L, h, g, m):        
    '''
    integral of hydrostatic equation over layer with linear temperature variation
    
    Args:
        pb: base level pressure
        tb: base level temp [K]
        L: lapse rate [deg/km]
        h: layer thickness [km]
        g: grav accel [m/s^2]
        m: molec wt [kg/kmole]
        
    Returns:
        hydrostatic results
    
    20151027 Scott Havens
     '''
    
    # the factors 1.e-3 and 1.e3 are for units conversion
    if L == 0:
        return pb * np.exp(-g * m * h * 1.e3/(RGAS * tb))
    else:
        return pb * np.power(tb/(tb + L * h), g * m/(RGAS * L * 1.e-3))
       

def satw(tk):
    '''
    Saturation vapor pressure of water. from IPW satw
    
    Args:
        tk: temperature in Kelvin
        
    Returns:
        saturated vapor pressure over water
        
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
        
    Args:
        tk: temperature in Kelvin
        
    Returns:
        saturated vapor pressure over ice
        
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
    Calculate atmosphere emissivity from Brutsaert (1975) :cite:`Brutsaert:1975`
    
    Args:
        ta: air temp (K)
        l: temperature lapse rate (deg/m)
        ea: vapor pressure (Pa)
        z: elevation (z)
        pa: air pressure (Pa)
        
    Returns:
        atmosphericy emissivity
    
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
    on a model by Marks and Dozier (1979) :citeL`Marks&Dozier:1979`.
    
    Args:
        ta: air temperature [C]
        tw: dew point temperature [C]
        z: elevation [m]
        skvfac: sky view factor
    
    Returns:
        Long wave (thermal) radiation corrected for terrain
    
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



def Garen2005(th, cloud_factor):
    """    
    Cloud correction is based on the relationship in Garen and Marks (2005) :cite:`Garen&Marks:2005` 
    between the cloud factor and measured long wave radiation using measurement stations in the Boise 
    River Basin. 

    .. math::
        L_{cloud} = L_{clear} * (1.485 - 0.488 * cloud\_factor)
    
    Args:
        th: clear sky thermal radiation [W/m2]
        cloud_factor: fraction of sky that are not clouds, 1 equals no clouds, 0 equals all clouds
    
    Returns:
        cloud corrected clear sky thermal radiation
        
    20170515 Scott Havens
    """
    
    return th * (1.485 - 0.488 * cloud_factor)


def Unsworth1975(th, ta, cloud_factor):
    """    
    Cloud correction is based on Unsworth and Monteith (1975) :cite:`Unsworth&Monteith:1975` 
    
    .. math::
            \epsilon_a = (1 - 0.84) \epsilon_{clear} + 0.84c
            
    where :math:`c = 1 - cloud\_factor`
    
    Args:
        th: clear sky thermal radiation [W/m2]
        ta: temperature in Celcius that the clear sky thermal radiation was calcualted from [C]
        cloud_factor: fraction of sky that are not clouds, 1 equals no clouds, 0 equals all clouds
        
    Returns:
        cloud corrected clear sky thermal radiation
        
    20170515 Scott Havens
    """
    
    c = 1 - cloud_factor
    ta = ta + FREEZE
    
    # calculate the clear sky emissivity
    ec = th/(STEF_BOLTZ * np.power(ta, 4))
    
    # adjsut the atmospheric emissivity for clouds
    ea = (1 - 0.84*c) * ec + 0.84*c
    
    return calc_long_wave(ea, ta)


def Kimball1982(th, ta, ea, cloud_factor):
    """
    Cloud correction is based on Kimball et al. (1982) :cite:`Kimball&al:1982`
     
    .. math::
        
        L_d &= L_{clear} + \\tau_8 c f_8 \sigma T^{4}_{c}
        
        \\tau_8 &= 1 - \epsilon_{8z} (1.4 - 0.4 \epsilon_{8z})
        
        \epsilon_{8z} &= 0.24 + 2.98 \\times 10^{-6} e^2_o exp(3000/T_o)
        
        f_8 &= -0.6732 + 0.6240 \\times 10^{-2} T_c - 0.9140 \\times 10^{-5} T^2_c
            
    where the original Kimball et al. (1982) :cite:`Kimball&al:1982` was for multiple cloud layers, which
    was simplified to one layer. :math:`T_c` is the cloud temperature and is assumed to be 11 K cooler
    than :math:`T_a`.
        
    Args:
        th: clear sky thermal radiation [W/m2]
        ta: temperature in Celcius that the clear sky thermal radiation was calcualted from [C]
        ea: distrubted vapor pressure [kPa]
        cloud_factor: fraction of sky that are not clouds, 1 equals no clouds, 0 equals all clouds
        
    Returns:
        cloud corrected clear sky thermal radiation
    
    20170515 Scott Havens
    """
    
    ta = ta + FREEZE
    Tc = ta - 11
    
    f8 = -0.6732 + 0.6240 * 10**(-2) * Tc - 0.9140 * 10**(-5) * Tc**2
    e8z = 0.24 + 2.98 * 10**(-6) * ea**2 * np.exp(3000/ta)
    t8 = 1 - e8z * (1.4 - 0.4 * e8z)
    
    return th + calc_long_wave(f8 * e8z * t8, ta)
    
    
def Crawford1999(th, ta, cloud_factor):
    """
    Cloud correction is based on Crawford and Duchon (1999) :cite:`Crawford&Duchon:1999`
    
    .. math::
            \epsilon_a = (1 - cloud\_factor) + cloud\_factor * \epsilon_{clear}
            
    where :math:`cloud\_factor` is the ratio of measured solar radiation to the clear sky irradiance.
    
    Args:
        th: clear sky thermal radiation [W/m2]
        ta: temperature in Celcius that the clear sky thermal radiation was calcualted from [C]
        cloud_factor: fraction of sky that are not clouds, 1 equals no clouds, 0 equals all clouds
        
    Returns:
        cloud corrected clear sky thermal radiation
    
    20170515 Scott Havens
    """

    return calc_long_wave(1 - cloud_factor, ta + FREEZE) + cloud_factor * th

