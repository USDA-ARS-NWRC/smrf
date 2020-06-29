import numpy as np

from smrf.envphys.constants import (FREEZE, GRAVITY, MOL_AIR, RGAS, SEA_LEVEL,
                                    STD_LAPSE, STD_LAPSE_M, STEF_BOLTZ)
from smrf.envphys.vapor_pressure import sati


def brutsaert(air_temp, lapse_rate, vapor_pressure, elevation, pressure):
    """
    Calculate atmosphere emissivity from Brutsaert (1975):cite:`Brutsaert:1975`

    Args:
        air_temp: air temp (K)
        lapse_rate: temperature lapse rate (deg/m)
        ea: vapor pressure (Pa)
        elevation: elevation (z)
        pressure: air pressure (Pa)

    Returns:
        atmosphericy emissivity

    20151027 Scott Havens
    """

    t_prime = air_temp - (lapse_rate * elevation)
    rh = vapor_pressure / sati(air_temp)
    rh[rh > 1] = 1

    e_prime = (rh * sati(t_prime)) / 100.0

    air_emiss = (1.24 * np.power(e_prime / t_prime, 1. / 7.0)) * \
        pressure / SEA_LEVEL

    air_emiss[air_emiss > 1.0] = 1.0

    return air_emiss


def hysat(pb, tb, L, h, g, m):
    """
    integral of hydrostatic equation over layer with linear temperature
    variation

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
     """

    # the factors 1.e-3 and 1.e3 are for units conversion
    if L == 0:
        return pb * np.exp(-g * m * h * 1.e3/(RGAS * tb))
    else:
        return pb * np.power(tb/(tb + L * h), g * m/(RGAS * L * 1.e-3))


def topotherm(ta, tw, z, skvfac):
    """
    Calculate the clear sky thermal radiation.  topotherm calculates  thermal
    radiation from the atmosphere corrected for topographic effects, from near
    surface air temperature Ta, dew point temperature DPT, and elevation. Based
    on a model by Marks and Dozier (1979) :citeL`Marks&Dozier:1979`.

    Args:
        ta: air temperature [C]
        tw: dew point temperature [C]
        z: elevation [m]
        skvfac: sky view factor

    Returns:
        Long wave (thermal) radiation corrected for terrain

    20151027 Scott Havens
    """

    # convert ta and tw from C to K
    ta = ta + FREEZE
    tw = tw + FREEZE

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
    T0 = ta - (z * STD_LAPSE_M)

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
