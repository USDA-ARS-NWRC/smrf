'''
Created on March 14, 2017
Originally written by Scott Havens in 2015
@author: Micah Johnson
'''

__version__ = '0.2.1'

import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt


'''
When creating a new NASDE model make sure you adhere to the following:

1. Add a new method here with a unique name.
2. Add your method to the available_models dictionary using the format of the
expected config file string followed by your function name
3. Document and run smrf!
'''

def calc_phase_and_density(temperature, precipitation, nasde_model):
    '''
    Uses various new accumulated snow density models to estimate the snow
    density of precipitation that falls during sub-zero conditions.
    The models all are based on the dew point temperature and the amount of
    precipitation, All models used here must return a dictionary containing the
    keywords pcs and rho_s for percent snow and snow density respectively.

    Args:
        temperature - a single timestep of the distributed dew point temperature

        precip - Numpy array of the distributed precipitation

        nasde_model - string value set in the configuration file representing the method
                    for estimating density of new snow that has just fallen.

    Returns:
        snow_density - an numpy array of snow density matching the domain size.

    '''
    # convert the inputs to numpy arrays
    precip = np.array(precipitation)
    temperature = np.array(temperature)

    snow_density = np.zeros(precip.shape)
    perc_snow = np.zeros(precip.shape)
    #New accumulated snow point models can go here.

    if nasde_model in available_models.keys():
        result = available_models[nasde_model](temperature,precip)
    else:
        raise ValueError("{0} is not an implemented new accumulated snow density model (NASDE)! Check the config file under precipitation".format(nasde_model))

    snow_density = result['rho_s']
    perc_snow = result['pcs']

    return snow_density,perc_snow


def calc_perc_snow(Tpp, Tmax=0.0, Tmin=-10.0):
    """
    Numpy implementation of the calc_perc_snow
    """

    #Coefficients for snow relationship
    Tr0 = 0.5
    Pcr0 = 0.25
    Pc0 = 0.75

    # this shouldn't have to be done again unless it's outside this module
    # We can set a flag later if it should be checked
    #Set a cap on temperature
#     Tpp, tsnow = check_temperature(Tpp, Tmax = Tmax, Tmin = Tmin)


    pcs = np.zeros(Tpp.shape)

    pcs[Tpp <= -0.5] = 1.0

    ind = (Tpp > -0.5) & (Tpp <= 0.0)
    if np.any(ind):
        pcs[ind] = (-Tpp[ind] / Tr0) * Pcr0 + Pc0

    ind = (Tpp > 0.0) & (Tpp <= Tmax +1.0)
    if np.any(ind):
        pcs[ind] = (-Tpp[ind] / (Tmax + 1.0)) * Pc0 + Pc0

    return pcs


def check_temperature(Tpp, Tmax = 0.0, Tmin = -10.0):
    """
    set precipitation temperature, % snow, and SWE
    """

    Tpp[Tpp < Tmin] = Tmin

    tsnow = Tpp.copy()
    tsnow[Tpp > Tmax] = Tmax

    return Tpp, tsnow


#===============================================================================
# BEGIN NASDE MODELS HERE AND BELOW
#===============================================================================

def susong1999(temperature, precipitation):
    '''
    Follows the IPW command mkprecip

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
    precipitation - array of precipitation values [mm]
    temperature - array of temperature values, use dew point temperature
        if available [degree C]

    Output:
    - returns the percent snow and estimated snow density
    '''

    # create a list from the table above
    t = []
    t.append( {'temp_min': -1e309,  'temp_max': -5,     'snow': 1,    'density':75} )
    t.append( {'temp_min': -5,      'temp_max': -3,     'snow': 1,    'density':100} )
    t.append( {'temp_min': -3,      'temp_max': -1.5,    'snow': 1,    'density':150} )
    t.append( {'temp_min': -1.5,    'temp_max': -0.5,   'snow': 1,    'density':175} )
    t.append( {'temp_min': -0.5,    'temp_max': 0.0,    'snow': 0.75, 'density':200} )
    t.append( {'temp_min': 0.0,     'temp_max': 0.5,    'snow': 0.25, 'density':250} )
    t.append( {'temp_min': 0.5,     'temp_max': 1e309,  'snow': 0,    'density':0} )


    # preallocate the percent snow (ps) and snow density (sd)
    ps = np.zeros(precipitation.shape)
    sd = np.zeros(ps.shape)

    # if no precipitation return all zeros
    if np.sum(precipitation) == 0:
        return ps, sd

    # determine the indicies and allocate based on the table above
    for row in t:

        # get the values between the temperature ranges that have precip
        ind = [(temperature >= row['temp_min']) & (temperature < row['temp_max'])]

        # set the percent snow
        ps[ind] = row['snow']

        # set the density
        sd[ind] = row['density']


    # if there is no precipitation at a pixel, don't report a value
    # this may make isnobal crash, I'm not really sure
    ps[precipitation == 0] = 0
    sd[precipitation == 0] = 0

    return {'pcs':ps, 'rho_s':sd}


def continuous_susong1999(Tpp, precip, Tmax = 0.0, Tmin = -10.0, check_temps=True):
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
    ex_max = 1.75
    exr = 0.75
    ex_min = 1.0

    Tz = 0.0

    # again, this shouldn't be needed in this context
    if check_temps:
        Tpp, tsnow = check_temperature(Tpp, Tmax=Tmax, Tmin=Tmin)

    pcs = calc_perc_snow(Tpp,Tmin=Tmin, Tmax = Tmax)

    # new snow density - no compaction
    Trange = Tmax - Tmin
    ex = ex_min + (((Trange + (tsnow - Tmax)) / Trange) * exr)

    ex[ex > ex_max] = ex_max

    rho_ns = 50.0 + (1.7 * ((Tpp-Tz) + 15.0)**ex)

    return {'pcs':pcs, 'rho_s':rho_ns}


def marks2017(Tpp, pp):

    """
    Numpy implementation of the compacted_snow_density
    """

    # TODO check that the Tpp==tsnow, the check_temperature seems to make
    # them equal

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

    rho_ns = d_rho_m = d_rho_c = zs = rho_s = swe = pcs = np.zeros(Tpp.shape)
    rho = np.ones(Tpp.shape)

    if np.any(pp > 0):

        # check the precipitation temperature
        Tpp, tsnow = check_temperature(Tpp, Tmax=Tmax, Tmin=Tmin)

        # Calculate the percent snow and initial uncompacted density
        result = continuous_susong1999(Tpp,pp,Tmax=Tmax, Tmin=Tmin)
        pcs = result['pcs']
        rho_orig = result['rho_s']

        swe = pp * pcs

        # Calculate the density only where there is swe
        swe_ind = swe > 0.0
        if np.any(swe_ind):

            s_pcs = pcs[swe_ind]
            s_pp = pp[swe_ind]
            s_swe = swe[swe_ind]
            s_tpp = Tpp[swe_ind] # transforms to a 1D array, will put back later
            s_tsnow = tsnow[swe_ind] # transforms to a 1D array, will put back later

            s_rho_ns = rho_orig[swe_ind] # transforms to a 1D array, will put back later

            #Convert to a percentage of water
            s_rho_ns /= water

            # proportional total storm mass compaction
            s_d_rho_c = (0.026 * np.exp(-0.08 * (Tz - s_tsnow)) * s_swe * np.exp(-21.0 * s_rho_ns))

            ind = s_rho_ns * water > 100.0
            c11 = np.ones(s_rho_ns.shape)

            c11[ind] = (c_min + ((Tz - s_tsnow[ind]) * cfac)) + 1.0

            s_d_rho_m = 0.01 * c11 * np.exp(-0.04 * (Tz - s_tsnow))

            # compute snow density, depth & combined liquid and snow density
            s_rho_s = s_rho_ns +((s_d_rho_c + s_d_rho_m) * s_rho_ns)

            s_zs = s_swe / s_rho_s

            # a mixture of snow and liquid
            s_rho = s_rho_s.copy()
            mix = (s_swe < s_pp) & (s_pcs > 0)
            if np.any(mix):
                s_rho[mix] = (s_pcs[mix] * s_rho_s[mix]) + (1.0 - s_pcs[mix])

            s_rho[s_rho > 1.0] = 1.0

            # put the values back into the larger array
            rho_ns[swe_ind] = s_rho_ns
            d_rho_m[swe_ind] = s_d_rho_m
            d_rho_c[swe_ind] = s_d_rho_c
            zs[swe_ind] = s_zs
            rho_s[swe_ind]= s_rho_s
            rho[swe_ind] = s_rho
            pcs[swe_ind] = s_pcs

    # # convert densities from proportions, to kg/m^3 or mm/m^2
    rho_ns = rho_ns * water
    rho_s = rho_s * water
    rho = rho * water


    return {'swe':swe, 'pcs':pcs,'rho_ns': rho_ns, 'd_rho_c' : d_rho_c, 'd_rho_m' : d_rho_m, 'rho_s' : rho_s, 'rho':rho, 'zs':zs}


#Add NASDE models here to ensure smrf visibility.
available_models = {
        'susong1999':susong1999,
        'continuous_susong1999':continuous_susong1999,
        'marks2017':marks2017
        }

if __name__ == '__main__':
    print("\nNothing implemented here.")
