'''
Created on March 14, 2017
Originally written by Scott Havens in 2015
@author: Micah Johnson
'''

__version__ = '0.1.1'

import numpy as np
import pandas as pd
def mkprecip(precipitation, temperature):
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

    # convert the inputs to numpy arrays
    precipitation = np.array(precipitation)
    temperature = np.array(temperature)

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

    return ps, sd

def calc_density(precip, temperature, use_compaction = True):
    """
    Uses a new snow density model to calculate the snow density based on the
    storm total and considers compaction, liquid water effects, temperature.

    Meant to be used after the fact when all the data is available.


    args:
    precip - netcdf array of precip across the whole basin. If compaction is
            this array should be the accumulated precip, otherwise it should be
            hourly precip.

    temperature - a single timestep of distributed temperature

    use_compaction - determines whether the snow model will account for compaction
                that could occur during a storm in addition to using the oringal
                temperature based model.
    returns:
    snow_density - an array of snow density matching the domain size.
    """

    snow_density = np.zeros(precip.shape)
    x_len = len(snow_density)
    y_len = len(snow_density[0])
    for (i,j), pp in np.ndenumerate(precip):
        tpp  = temperature[i][j]
        if use_compaction:
            snow_density[i][j] = (compacted_snow_density(tpp,pp))['rho_s']
        else:
            snow_density[i][j] = (fresh_snow_density(tpp,pp))['rho_ns']

    return snow_density

def compacted_snow_density(Tpp,pp):
    """
    Snow density point model that takes into account the hourly temperature during precip
    and the total storm accumulated_precip.

    args:
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
        if Tpp < Tmin:
            Tpp = Tmin
            tsnow = Tmin
        else :
            if Tpp > Tmax:
                tsnow = Tmax
            else:
                tsnow = Tpp

        if Tpp <= -0.5:
            pcs = 1.0

        elif Tpp > -0.5 and Tpp <= 0.0:
            pcs = (((-Tpp) / Tr0) * Pcr0) + Pc0

        elif Tpp > 0.0 and Tpp <= (Tmax +1.0):
            pcs = (((-Tpp) / (Tmax + 1.0)) * Pc0) + Pc0

        else:
            pcs = 0.0

        swe = pp * pcs

        if swe > 0.0:
            # new snow density - no compaction
            Trange = Tmax - Tmin
            ex = ex_min + (((Trange + (tsnow - Tmax)) / Trange) * exr)

            if ex > ex_max:
                ex = ex_max

            rho_ns = (50.0 + (1.7 * (((Tpp - Tz) + 15.0)**ex))) / water

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
    print "\nNothing implemented here."
