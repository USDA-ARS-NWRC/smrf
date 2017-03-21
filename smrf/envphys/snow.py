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

def compacted_snow_density(accumulated_precip, temperature):
    """
    Uses a new snow density model to calculate the snow density based on the
    storm total, considers compaction, liquid water effects, temperature.

    Meant to be used after the fact when all the data is available.


    args:
    accumulated_precip - the distributed total precip accumulated during a storm

    temperature - a single timestep of distributed temperature
    """
    x_len = len(precip[0][:])
    y_len = len(precip[:][0])
    snow_density = np.zeros((y_len,x_len))
    for i in range(y_len):
        for j in range(x_len):
            pp = accumulated_precip[i][j]
            tpp  = temperature[i][j]
            snow_density[i][j] = snow_rho(tpp,pp)

    return snow_density

def snow_rho(Tpp,pp):
	ex_max = 1.75
	exr = 0.75
	ex_min = 1.0
	c1_min = 0.026
	c1_max = 0.069
	c1r = 0.043
	Tmin = -10.0
	Tmax = +1.0
	Tz = 0.0
	Tr0 = 0.5
	Pcr0 = 0.25
	Pc0 = 0.75

	water = 1000.0
	if Tpp < Tmin:
		Tpp = Tmin

	if Tpp <= -0.5:
		pcs = 1.0

	elif Tpp > -0.5 and Tpp <= 0.0:
		pcs = (((-Tpp) / Tr0) * Pcr0) + Pc0

	elif Tpp > 0.0 and Tpp <= 1.0:
		pcs = Tpp * Pc0

	else:
		pcs = 0.0

	swe = pp * pcs

	Trange = Tmax - Tmin

	c1 = c1_min + (((Trange + (Tpp - Tmax)) / Trange) * c1r)
	ex = ex_min + (((Trange + (Tpp - Tmax)) / Trange) * exr)

	#exponentials in python are done using a double *
	rho_ns = (50.0 + (1.7 * (((Tpp - Tz) + 15.0)**ex))) / water

	d_rho_c = (0.026 * np.exp(-0.08 * (Tz - Tpp)) * swe * np.exp(-21.0 * rho_ns))

	if rho_ns * water < 100.0:
		c11 = 1.0
	else:
		c11 = np.exp(-0.046 * ((rho_ns * water) - 100.0))

	d_rho_m = 0.01 * c11 * np.exp(-0.04 * (Tz - Tpp))

	rho_s = rho_ns +((d_rho_c + d_rho_m) * rho_ns)
	zs = swe / rho_s

	if swe < pp and zs != 0:
		rho = pp / zs
	else:
		rho = rho_s

	return rho


if __name__ == '__main__':
    from netCDF4 import Dataset
    from matplotlib import pyplot as plt
    import time

    start = time.time()
    pds =Dataset('/home/micahjohnson/Desktop/test_output/precip.nc','r')
    sds =Dataset('/home/micahjohnson/Desktop/test_output/snow_density.nc','r')

    dds =Dataset('/home/micahjohnson/Desktop/test_output/dew_point.nc','r')
    precip = pds.variables['precip'][111]
    dpt = dds.variables['dew_point'][111]
    srho = sds.variables['snow_density'][111]

    pds.close()
    dds.close()
    sds.close()

    snow_density = compacted_snow_density(precip,dpt)

    #visual
    fig = plt.figure()
    a=fig.add_subplot(1,2,1)
    plt.imshow(snow_density)
    a.set_title('New Snow Density')

    # a=fig.add_subplot(1,2,2)
    # plt.imshow(srho)
    # a.set_title('Original Snow density')
    plt.colorbar()
    print "Single time step took {0}s".format(time.time() - start)
    plt.show()
