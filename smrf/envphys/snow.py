'''
Created on March 14, 2017
Originally written by Scott Havens in 2015
@author: Micah Johnson
'''

__version__ = '0.2.1'

import numpy as np
import pandas as pd

def calc_phase_and_density(precip, temperature, nasde_model):
    '''
    Uses various new accumulated snow density models to estimate the snow
    density of precipitation that falls during sub-zero conditions.
    The models all are based on the dew point temperature and the amount of
    precipitation, All models used here must return a dictionary containing the
    keywords pcs and rho_s for percent snow and snow density respectively.

    Args:
        precip - Numpy array of the distributed precipitation
        temperature - a single timestep of the distributed dew point temperature

        nasde_model - string value set in the configuration file representing the method
                    for estimating density of new snow that has just fallen.

    Returns:
        snow_density - an numpy array of snow density matching the domain size.

    '''

    snow_density = np.zeros(precip.shape)
    perc_snow = np.zeros(precip.shape)

    x_len = len(snow_density)
    y_len = len(snow_density[0])
    for (i,j), pp in np.ndenumerate(precip):
        tpp  = temperature[i][j]

        #New accumulated snow point models can go here.
        if nasde_model == 'susong1999':
            result = susong1999(tpp)

        elif nasde_model == 'continuous_susong1999':
            result = continuous_susong1999(tpp)

        elif nasde_model == 'marks2017':
            result = marks2017(tpp,pp)
        else:
            raise ValueError("{0} is not an implemented NASDE model!".format(nasde_model))

        snow_density[i][j] = result['rho_s']
        perc_snow[i][j] = result['pcs']

    return snow_density,perc_snow

def continuous_susong1999(Tpp, Tmax = 0.0, Tmin = -10.0):
    '''
    Follows method susong1999 but is the continuous form of table shown there.
    The table was estimate by Danny Marks in 2017 which resulted in the
    piecewise equations below:

    Percent Snow:
         *  -0.5C < temperature < 0.0, percent snow = (((-temperature) / Tr0) * Pcr0) + Pc0
         *  0.0C < temperature < Max temperature + 1.0, percent snow = -(((-Tpp) / (Tmax + 1.0)) * Pc0) + Pc0

    Snow rho_s:
        *  (50.0 + (1.7 * ((temperature + 15.0) ^ ex)))
        Where:
        *  ex = ex_min + (((temperature_range + (temperature of snow - Max temperature)) / temperature range) * exr)
        *  ex > 1.75, ex = 1.75

    Args:
        temperature - point value of temperature, use dew point temperature
        if available [degree C]

    Returns:
        result - A dictionary that containing the percent snow (0.0-1.0) and the new snow density (kg/m^3),
                which are labelled as pcs and rho_s respectively
    '''
    #Snow Model constants
    ex_max = 1.75
    exr = 0.75
    ex_min = 1.0
    c1_min = 0.026
    c1_max = 0.069
    c1r = 0.043
    c_min = 0.0067
    cfac = 0.0013
    Tmin = -10.0
    Tmax = 0.0
    Tz = 0.0
    Tr0 = 0.5
    Pcr0 = 0.25
    Pc0 = 0.75

    Tz = 0.0

    Tpp,tsnow = check_temperature(Tpp,Tmax = Tmax, Tmin = Tmin)

    if Tpp <= -0.5:
        pcs = 1.0

    elif Tpp > -0.5 and Tpp <= 0.0:
        pcs = (((-Tpp) / Tr0) * Pcr0) + Pc0

    elif Tpp > 0.0 and Tpp <= (Tmax +1.0):
        pcs = (((-Tpp) / (Tmax + 1.0)) * Pc0) + Pc0

    else:
        pcs = 0.0

    # new snow density - no compaction
    Trange = Tmax - Tmin
    ex = ex_min + (((Trange + (tsnow - Tmax)) / Trange) * exr)

    if ex > ex_max:
        ex = ex_max

    rho_ns = (50.0 + (1.7 * (((Tpp - Tz) + 15.0)**ex)))
    return {'pcs':pcs, 'rho_s':rho_ns}


def check_temperature(Tpp, Tmax = 0.0, Tmin = -10.0):
    # set precipitation temperature, % snow, and SWE
    if Tpp < Tmin:
        Tpp = Tmin
        tsnow = Tmin
    else:
        if Tpp > Tmax:
            tsnow = Tmax
        else:
            tsnow = Tpp
    return Tpp, tsnow


def susong1999(temperature):
    '''
    Follows the IPW command mkprecip except this is a point model version.

    The precipitation phase, or the amount of precipitation falling as rain or snow, can significantly
    alter the energy and mass balance of the snowpack, either leading to snow accumulation or inducing
    melt :cite:`Marks&al:1998` :cite:`Kormos&al:2014`. The precipitation phase and initial snow density are
    based on the precipitation temperature (the distributed dew point temperature) and are estimated
    after Susong et al (1999) :cite:`Susong&al:1999`. The table below shows the relationship to
    precipitation temperature:

    ========= ======== ============ ===============
    Min Temp  Max Temp Percent snow Snow density
    [deg C]   [deg C]  [%]          [kg/m^3]
    ========= ======== ============ ===============
    -Inf      -5       100          75
    -5        -3       100          100
    -3        -1.5     100          150
    -1.5      -0.5     100          175
    -0.5      0        75           200
    0         0.5      25           250
    0.5       Inf      0            0
    ========= ======== ============ ===============

    Args:
        temperature - point value of temperature, use dew point temperature
        if available [degree C]

    Returns:
        result - A dictionary that containing the percent snow (0.0-1.0) and the new snow density (kg/m^3)
    '''

    # create a list from the table above
    t = []

    t.append( {'temp_min': -1e309,  'temp_max': -5,     'pcs': 1.0,    'rho_s':75.0} )
    t.append( {'temp_min': -5,      'temp_max': -3,     'pcs': 1.0,    'rho_s':100.0} )
    t.append( {'temp_min': -3,      'temp_max': -1.5,    'pcs': 1.0,    'rho_s':150.0} )
    t.append( {'temp_min': -1.5,    'temp_max': -0.5,   'pcs': 1.0,    'rho_s':175.0} )
    t.append( {'temp_min': -0.5,    'temp_max': 0.0,    'pcs': 0.75, 'rho_s':200.0} )
    t.append( {'temp_min': 0.0,     'temp_max': 0.5,    'pcs': 0.25, 'rho_s':250.0} )
    t.append( {'temp_min': 0.5,     'temp_max': 1e309,  'pcs': 0.0,    'rho_s':0.0} )

    # determine the indicies and allocate based on the table above
    for row in t:

        # get the values between the temperature ranges that have precip
        if temperature >= row['temp_min'] and temperature < row['temp_max']:
            result = row
            break

    return result

def marks2017(Tpp,pp):
    """
    New accumulated Snow density point model that takes into account the hourly temperature during precip
    and the total storm accumulated_precip.

    Args:
    Tpp - a single value of the hourly temperature during the storm

    pp - a single value of the accumulated_precip precip during a storm

    Returns:
    swe, pcs, rho_ns, d_rho_c, d_rho_m, rho_s, rho, zs

    Tpp - temperature during precip
    pp - precipitation accumulated
    swe - snow water equivalent
    pcs - percent snow
    rho_ns - density of new snow with out compaction
    d_rho_c -
    d_rho_m -
    rho_s - density of the snow with compaction
    rho - density of precip
    zs - snow height
    """

    ex_max = 1.75
    exr = 0.75
    ex_min = 1.0
    c1_min = 0.026
    c1_max = 0.069
    c1r = 0.043
    c_min = 0.0067
    cfac = 0.0013
    Tmin = -10.0
    Tmax = 0.0
    Tz = 0.0
    Tr0 = 0.5
    Pcr0 = 0.25
    Pc0 = 0.75

    water = 1000.0

    if pp > 0.0:
        # set precipitation temperature, % snow, and SWE
        Tpp, tsnow = check_temperature(Tpp, Tmax = Tmax, Tmin = Tmin)

        # Calculate the percent snow and new snow without compaction
        snow = continuous_susong1999(Tpp, Tmax = Tmax, Tmin = Tmin)
        pcs = snow['pcs']
        rho_ns = snow['rho_s']

        swe = pp * pcs

        if swe > 0.0:
            #Convert to a percentage of water
            rho_ns /= water
            # proportional total storm mass compaction
            d_rho_c = (0.026 * np.exp(-0.08 * (Tz - tsnow)) * swe * np.exp(-21.0 * rho_ns))

            if rho_ns * water < 100.0:
                c11 = 1.0
            else:
                #c11 = np.exp(-0.046 * ((rho_ns * water) - 100.0))
                c11 = (c_min + ((Tz - tsnow) * cfac)) + 1.0

            d_rho_m = 0.01 * c11 * np.exp(-0.04 * (Tz - tsnow))

            # compute snow denstiy, depth & combined liquid and snow density
            rho_s = rho_ns +((d_rho_c + d_rho_m) * rho_ns)

            zs = swe / rho_s

            if swe < pp:
                if pcs > 0.0:
                    rho = (pcs * rho_s) + (1 - pcs)
                if rho > 1.0:
                    rho = water / water

            else:
                rho = rho_s

        else:
            rho_ns = 0.0
            d_rho_m = 0.0
            d_rho_c = 0.0
            zs = 0.0
            rho_s = 0.0
            rho = water / water

        # convert densities from proportions, to kg/m^3 or mm/m^2
        rho_ns *= water
        rho_s *= water
        rho *= water

    #No precip
    else:
        rho_ns = 0.0
        d_rho_m = 0.0
        d_rho_c = 0.0
        zs = 0.0
        rho_s = 0.0
        rho = 0.0
        swe = 0.0
        pcs = 0.0

    result = {'swe':swe, 'pcs':pcs,'rho_ns': rho_ns, 'd_rho_c' : d_rho_c, 'd_rho_m' : d_rho_m, 'rho_s' : rho_s, 'rho':rho, 'zs':zs}

    return result


if __name__ == '__main__':
    print("\nNothing implemented here.")
