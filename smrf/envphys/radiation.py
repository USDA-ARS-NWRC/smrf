"""
Created on Apr 17, 2015
@author: scott
"""

import datetime
import logging
import math
import os
import subprocess as sp

import numpy as np
import pandas as pd
import pytz
from scipy.integrate import quad
from scipy.interpolate import Akima1DInterpolator

from smrf.envphys import sunang
from smrf.utils import utils
from smrf.utils.io import isint

on_rtd = os.environ.get('READTHEDOCS') == 'True'
if on_rtd:
    IPW = '.'  # placehold while building the docs
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
SOLAR_CONSTANT = 1368.0  # solar constant in W/m**2


def growth(t):
    """
    Calculate grain size growth
    From IPW albedo > growth
    """

    a = 4.0
    b = 3.
    c = 2.0
    d = 1.0

    factor = (a+(b*t)+(t*t))/(c+(d*t)+(t*t)) - 1.0

    return(1.0 - factor)


def albedo(telapsed, cosz, gsize, maxgsz, dirt=2):
    """
    Calculate the abedo, adapted from IPW function albedo

    Args:
        telapsed - time since last snow storm (decimal days)
        cosz - cosine local solar illumination angle matrix
        gsize - gsize is effective grain radius of snow after last storm (mu m)
        maxgsz - maxgsz is maximum grain radius expected from grain growth
                  (mu m)
        dirt - dirt is effective contamination for adjustment to visible
               albedo (usually between 1.5-3.0)

    Returns:
        tuple:
        Returns a tuple containing the visible and IR spectral albedo

        - **alb_v** (*numpy.array*) - albedo for visible specturm

        - **alb_ir** (*numpy.array*) -  albedo for ir spectrum

    Created April 17, 2015
    Modified July 23, 2015 - take image of cosz and calculate albedo for
        one time step
    Scott Havens

    """

#     telapsed = np.array(telapsed)

    # check inputs
    if gsize <= 0 or gsize > 500:
        raise Exception("unrealistic input: gsize=%i", gsize)

    if (maxgsz <= gsize or maxgsz > 2000):
        raise Exception("unrealistic input: maxgsz=%i", maxgsz)
    if 1 >= dirt >= 10:
        raise Exception("unrealistic input: dirt=%i", dirt)
#     if dirt <= 1:
#         raise Exception("unrealistic input: dirt=%i", dirt)

    # set initial grain radii for vis and ir
    radius_ir = math.sqrt(gsize)
    range_ir = math.sqrt(maxgsz) - radius_ir
    radius_v = math.sqrt(dirt * gsize)
    range_v = math.sqrt(dirt * maxgsz) - radius_v

    # calc grain growth decay factor
    growth_factor = growth(telapsed + 1.0)

    # calc effective gsizes for vis & ir
    gv = radius_v + (range_v * growth_factor)
    gir = radius_ir + (range_ir * growth_factor)

    # calc albedos for cos(z)=1
    alb_v_1 = MAXV - (gv / VFAC)
    alb_ir_1 = MAXIR * np.exp(IRFAC * gir)

    # calculate effect of cos(z)<1

    # adjust diurnal increase range
    dzv = gv * VZRG
    dzir = (gir * IRZRG) + IRZ0

    # calculate albedo
    alb_v = alb_v_1
    alb_ir = alb_ir_1

    # correct if the sun is up
    ind = cosz > 0.0
    alb_v[ind] += dzv[ind] * (1.0 - cosz[ind])
    alb_ir[ind] += dzir[ind] * (1.0 - cosz[ind])

    return alb_v, alb_ir


def decay_alb_power(veg, veg_type, start_decay, end_decay, t_curr, pwr, alb_v, alb_ir):
    """
    Find a decrease in albedo due to litter acccumulation. Decay is based on max
    decay, decay power, and start and end dates. No litter decay occurs before
    start_date. Fore times between start and end of decay,

    .. math::
      \\alpha = \\alpha - (dec_{max}^{\\frac{1.0}{pwr}} \\times \\frac{t-start}{end-start})^{pwr}

    Where :math:`\\alpha` is albedo, :math:`dec_{max}` is the maximum decay for albedo,
    :math:`pwr` is the decay power, :math:`t`, :math:`start`, and :math:`end` are the current,
    start, and end times for the litter decay.

    Args:
        start_decay: date to start albedo decay (datetime)
        end_decay: date at which to end albedo decay curve (datetime)
        t_curr: datetime object of current timestep
        pwr: power for power law decay
        alb_v: numpy array of albedo for visibile spectrum
        alb_ir: numpy array of albedo for IR spectrum

    Returns:
        tuple:
        Returns a tuple containing the corrected albedo arrays
        based on date, veg type
        - **alb_v** (*numpy.array*) - albedo for visible specturm

        - **alb_ir** (*numpy.array*) -  albedo for ir spectrum


    Created July 18, 2017
    Micah Sandusky

    """
    # Calculate hour past start of decay
    t_diff_hr = t_curr - start_decay
    t_diff_hr = t_diff_hr.days*24.0 + t_diff_hr.seconds/3600.0  # only need hours here
    # Calculate total time of decay
    t_decay_hr = (end_decay - start_decay)
    t_decay_hr = t_decay_hr.days*24.0 + \
        t_decay_hr.seconds/3600.0  # only need hours here
    # correct for veg
    alb_dec = np.zeros_like(alb_v)

    # Don't decay if before start
    if t_diff_hr <= 0.0:
        alb_dec = alb_dec * 0.0

    # Use max decay if after start
    elif t_diff_hr > t_decay_hr:
        # Use default
        alb_dec = alb_dec + veg['default']
        # Decay based on veg type
        for k, v in veg.items():
            if isint(k):
                alb_dec[veg_type == int(k)] = v

    # Power function decay if during decay period
    else:
        # Use defaults
        max_dec = veg['default']
        tao = (t_decay_hr) / (max_dec**(1.0/pwr))
        # Add default decay to array of zeros
        alb_dec = alb_dec + ((t_diff_hr) / tao)**pwr
        # Decay based on veg type
        for k, v in veg.items():
            max_dec = v
            tao = (t_decay_hr) / (max_dec**(1.0/pwr))
            # Set albedo decay at correct veg types
            if isint(k):
                alb_dec[veg_type == int(k)] = ((t_diff_hr) / tao)**pwr
                # self._logger.debug('Type {0}, decay {1}'.format(int(v), veg_type['veg'][v]))

    alb_v_d = alb_v - alb_dec
    alb_ir_d = alb_ir - alb_dec

    return alb_v_d, alb_ir_d


def decay_alb_hardy(litter, veg_type, storm_day, alb_v, alb_ir):
    """
    Find a decrease in albedo due to litter acccumulation
    using method from :cite:`Hardy:2000` with storm_day as input.

    .. math::
        lc = 1.0 - (1.0 - lr)^{day}

    Where :math:`lc` is the fractional litter coverage and :math:`lr` is the daily
    litter rate of the forest. The new albedo is a weighted average of the calculated albedo
    for the clean snow and the albedo of the litter.

    Note: uses input of l_rate (litter rate) from config
    which is based on veg type. This is decimal percent litter
    coverage per day

    Args:
        litter: A dictionary of values for default,albedo,41,42,43 veg types
        veg_type: An image of the basin's NLCD veg type
        storm_day: numpy array of decimal day since last storm
        alb_v: numpy array of albedo for visibile spectrum
        alb_ir: numpy array of albedo for IR spectrum
        alb_litter: albedo of pure litter

    Returns:
        tuple:
        Returns a tuple containing the corrected albedo arrays
        based on date, veg type
        - **alb_v** (*numpy.array*) - albedo for visible specturm

        - **alb_ir** (*numpy.array*) -  albedo for ir spectrum

    Created July 19, 2017
    Micah Sandusky

    """
    # array for decimal percent snow coverage
    sc = np.zeros_like(alb_v)
    # calculate snow coverage default veg type
    l_rate = litter['default']
    alb_litter = litter['albedo']

    sc = sc + (1.0-l_rate)**(storm_day)
    # calculate snow coverage based on veg type
    for k, v in litter.items():
        # self._logger.debug('litter {0}: {1}'.format(v, self.config['litter'][v] ) )
        l_rate = litter[k]
        if isint(k):
            sc[veg_type == int(k)] = (
                1.0 - l_rate)**(storm_day[veg_type == int(k)])
    # calculate litter coverage
    lc = np.ones_like(alb_v) - sc
    # weighted average to find decayed albedo
    alb_v_d = alb_v*sc + alb_litter*lc
    alb_ir_d = alb_ir*sc + alb_litter*lc

    return alb_v_d, alb_ir_d


def ihorizon(x, y, Z, azm, mu=0, offset=2, ncores=0):
    """
    Calculate the horizon values for an entire DEM image
    for the desired azimuth

    Assumes that the step size is constant

    Args:
        X - vector of x-coordinates
        Y - vector of y-coordinates
        Z - matrix of elevation data
        azm - azimuth to calculate the horizon at
        mu - 0 -> calculate cos(z)
             - >0 -> calculate a mask whether or not the point can see the sun

    Returns:
        H   - if mask=0 cosine of the local horizonal angles
            - if mask=1 index along line to the point

    20150602 Scott Havens
    """

    # check inputs
    azm = azm*np.pi/180  # degress to radians
    m, n = Z.shape

    # transform the x,y into the azm direction xr,yr
    xi, yi = np.arange(-n/2, n/2), np.arange(-m/2, m/2)
    X, Y = np.meshgrid(xi, yi)
    xr = X*np.cos(azm) - Y*np.sin(azm)
    yr = X*np.sin(azm) + Y*np.cos(azm)

    # xr is the "new" column index for the profiles
    # yr is the distance along the profile
    xr = xr.round().astype(int)
    yr = (x[2] - x[1]) * yr

    H = np.zeros(Z.shape)
#     pbar = progressbar.ProgressBar(n).start()
#     j = 0

    # loop through the columns
#     if ncores == 0:
    for i in np.arange(-n/2, n/2):
        find_horizon(i, H, xr, yr, Z, mu)

#     else:
#     shared_array_base = mp.Array(ctypes.c_double, m*n)
#     sH = np.ctypeslib.as_array(shared_array_base.get_obj())
#     sH = sH.reshape(m, n)
#     sxr = np.ctypeslib.as_array(shared_array_base.get_obj())
#     sxr = sxr.reshape(m, n)
#     syr = np.ctypeslib.as_array(shared_array_base.get_obj())
#     syr = syr.reshape(m, n)
#     sZ = np.ctypeslib.as_array(shared_array_base.get_obj())
#     sZ = sZ.reshape(m, n)
#     def wrap_horizon(i, def_param1=sH, def_parm2=sxr, def_param3=syr, def_param4=sZ):
#         find_horizon(i, sH, sxr, syr, sZ, 0.67)

#     pool = mp.Pool(processes=4)
#     [pool.apply(find_horizon, args=(i, shared_array, xr, yr, Z, mu, offset)) for i in range(-n/2,n/2)]
#     pool.map(wrap_horizon, range(-n/2,n/2))

#     print(shared_array)

    return H


def find_horizon(i, H, xr, yr, Z, mu):
    # index to profile and get the elevations
    ind = xr == i
    zi = Z[ind]

    # distance along the profile
    di = yr[ind]

    # sort the y values and get the cooresponding elevation
    idx = np.argsort(di)
    di = di[idx]
    zi = zi[idx]

    # if there are some values in the vector
    # calculate the horizons
    if len(zi) > 0:
        # h2 = hor1f_simple(di, zi)
        h = hor1f(di, zi)

        cz = _cosz(di, zi, di[h], zi[h])

        # if we are making a mask
        if mu > 0:
            # iz = cz == 0    # points that are their own horizon
            idx = cz > mu   # points sheltered from the sun
            cz[idx] = 0
            cz[~idx] = 1
#                 cz[iz] = 1

    H[ind] = cz

#         j += 1
#         pbar.update(j)
#     pbar.finish()


def hord(z):
    """
    Calculate the horizon pixel for all x,z
    This mimics the simple algorthim from Dozier 1981
    to help understand how it's working

    Works backwards from the end but looks forwards for
    the horizon 90% faster than rad.horizon

    Args::
        x - horizontal distances for points
        z - elevations for the points

    Returns:
        h - index to the horizon point

    20150601 Scott Havens
    """

    N = len(z)  # number of points to look at
#     offset = 1      # offset from current point to start looking

    # preallocate the h array
    h = np.zeros(N, dtype=int)
    h[N-1] = N-1
    i = N - 2

    # work backwarks from the end for the pixels
    while i >= 0:
        h[i] = i
        j = i + 1   # looking forward
        max_tan = -9999

        while j < N:
            sij = _slope_all(i, z[i], j, z[j])

            if sij > max_tan:
                h[i] = j
                max_tan = sij

            j = j + 1
        i = i - 1

    return h


def hor1f_simple(z):
    """
    Calculate the horizon pixel for all x,z
    This mimics the simple algorthim from Dozier 1981
    to help understand how it's working

    Works backwards from the end but looks forwards for
    the horizon 90% faster than rad.horizon

    Args:
        x - horizontal distances for points
        z - elevations for the points

    Returns:
        h - index to the horizon point

    20150601 Scott Havens
    """

    N = len(z)  # number of points to look at
#     offset = 1      # offset from current point to start looking

    # preallocate the h array
    h = np.zeros(N, dtype=int)
    h[N-1] = N-1
    i = N - 2

    # work backwarks from the end for the pixels
    while i >= 0:
        h[i] = i
        j = i + 1   # looking forward
        max_tan = 0

        while j < N:
            sij = _slope(i, z[i], j, z[j])

            if sij > max_tan:
                h[i] = j
                max_tan = sij

            j = j + 1
        i = i - 1

    return h


def hor1f(x, z, offset=1):
    """
    BROKEN: Haven't quite figured this one out

    Calculate the horizon pixel for all x,z
    This mimics the algorthim from Dozier 1981 and the
    hor1f.c from IPW

    Works backwards from the end but looks forwards for
    the horizon

    xrange stops one index before [stop]

    Args:
        x - horizontal distances for points
        z - elevations for the points

    Returns:
        h - index to the horizon point

    20150601 Scott Havens
    """

    N = len(x)  # number of points to look at
    x = np.array(x)
    z = np.array(z)

    # preallocate the h array
    h = np.zeros(N, dtype=int)
    h[N-1] = N-1    # the end point is it's own horizon

    # work backwarks from the end for the pixels
    for i in range(N-2, -1, -1):

        zi = z[i]

        # Start with next-to-adjacent point in either forward or backward
        # direction, depending on which way loop is running. Note that we
        # don't consider the adjacent point; this seems to help reduce noise.
        k = i + offset

        if k >= N:
            k -= 1

        # loop until horizon is found
        # xrange will set the maximum number of iterations that can be
        # performed based on the length of the vector
        for t in range(k, N):
            j = k
            k = h[j]

            sij = _slope(x[i], zi, x[j], z[j])
            sihj = _slope(x[i], zi, x[k], z[k])

            # if slope(i,j) >= slope(i,h[j]), horizon has been found; otherwise
            # set j to k (=h[j]) and loop again
            # or if we are at the end of the section
            if sij > sihj:  # or k == N-1:
                break

        # if slope(i,j) > slope(j,h[j]), j is i's horizon; else if slope(i,j)
        # is zero, i is its own horizon; otherwise slope(i,j) = slope(i,h[j])
        # so h[j] is i's horizon
        if sij > sihj:
            h[i] = j
        elif sij == 0:
            h[i] = i
        else:
            h[i] = k

    return h


def _slope(xi, zi, xj, zj):
    """
    Slope between the two points only if the pixel is higher
    than the other
    20150603 Scott Havens
    """

    return 0 if zj <= zi else (zj - zi) / (xj - float(xi))


def _slope_all(xi, zi, xj, zj):
    """
    Slope between the two points only if the pixel is higher
    than the other
    20150603 Scott Havens
    """

    return (zj - zi) / (xj - float(xi))


def _cosz(x1, z1, x2, z2):
    """
    Cosize of the zenith between two points

    20150601 Scott Havens
    """
    d = np.sqrt((x2 - x1)**2 + (z2 - z1)**2)
    diff = z2 - z1

#     v = np.where(diff != 0., d/diff, 100)

    i = d == 0
    d[i] = 1
    v = diff/d
    v[i] = 0

    return v


def shade(slope, aspect, azimuth, cosz=None, zenith=None):
    """
    Calculate the cosize of the local illumination angle over a DEM

    Solves the following equation
    cos(ts) = cos(t0) * cos(S) + sin(t0) * sin(S) * cos(phi0 - A)

    where
        t0 is the illumination angle on a horizontal surface
        phi0 is the azimuth of illumination
        S is slope in radians
        A is aspect in radians

    Slope and aspect are expected to come from the IPW gradient command.
    Slope is stored as sin(S) with range from 0 to 1. Aspect is stored
    as radians from south (aspect 0 is toward the south) with range from
    -pi to pi, with negative values to the west and positive values to the east

    Args:
        slope: numpy array of sine of slope angles
        aspect: numpy array of aspect in radians from south
        azimuth: azimuth in degrees to the sun -180..180 (comes from sunang)
        cosz: cosize of the zeinith angle 0..1 (comes from sunang)
        zenith: the solar zenith angle 0..90 degrees

    At least on of the cosz or zenith must be specified.  If both are
    specified the zenith is ignored

    Returns:
        mu: numpy matrix of the cosize of the local illumination angle cos(ts)

    The python shade() function is an interpretation of the IPW shade()
    function and follows as close as possible.  All equations are based
    on Dozier & Frew, 1990. 'Rapid calculation of Terrain Parameters For
    Radiation Modeling From Digitial Elevation Data,' IEEE TGARS

    20150106 Scott Havens
    """

    # process the options
    if cosz is not None:
        if (cosz <= 0) or (cosz > 1):
            raise Exception('cosz must be > 0 and <= 1')

        ctheta = cosz
        zenith = np.arccos(ctheta)  # in radians
        stheta = np.sin(zenith)

    elif zenith is not None:
        if (zenith < 0) or (zenith >= 90):
            raise Exception('Zenith must be >= 0 and < 90')

        zenith *= np.pi/180.0  # in radians
        ctheta = np.cos(zenith)
        stheta = np.sin(zenith)

    else:
        raise Exception('Must specify either cosz or zenith')

    if (azimuth > 180) or (azimuth < -180):
        raise Exception('Azimuth must be between -180 and 180 degrees')

    azimuth *= np.pi/180

    # get the cos S from cos^2 + sin^s = 1
    costbl = np.sqrt((1 - slope) * (1 + slope))

    # cosine of local illumination angle
    # mu = ctheta * costbl[s] + stheta * sintbl[s] * cosdtbl[a]
    mu = ctheta * costbl + stheta * slope * np.cos(azimuth - aspect)

    mu[mu < 0] = 0
    mu[mu > 1] = 1

    return mu


def shade_thread(queue, date, slope, aspect, zenith=None):
    """
    See shade for input argument descriptions

    Args:
        queue: queue with illum_ang, cosz, azimuth
        date_time: loop through dates to accesss queue

    20160325 Scott Havens
    """

    for v in ['cosz','azimuth','illum_ang']:
        if v not in queue.keys():
            raise ValueError('Queue must have {} key'.format(v))


    log = logging.getLogger(__name__)

    for t in date:

        log.debug('%s Calculating illumination angle' % t)

        mu = None
        cosz = queue['cosz'].get(t)

        if cosz > 0:
            azimuth = queue['azimuth'].get(t)
            mu = shade(slope, aspect, azimuth, cosz, zenith)

        queue['illum_ang'].put([t, mu])


def deg_to_dms(deg):
    """
    Decimal degree to degree, minutes, seconds
    """
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]


def cf_cloud(beam, diffuse, cf):
    """
    Correct beam and diffuse irradiance for cloud attenuation at a single
    time, using input clear-sky global and diffuse radiation calculations
    supplied by locally modified toporad or locally modified stoporad

    Args:
        beam: global irradiance
        diffuse: diffuse irradiance
        cf: cloud attenuation factor - actual irradiance / clear-sky irradiance

    Returns:
        c_grad: cloud corrected gobal irradiance
        c_drad: cloud corrected diffuse irradiance

    20150610 Scott Havens - adapted from cloudcalc.c
    """

    # define some constants
    CRAT1 = 0.15
    CRAT2 = 0.99
    CCOEF = 1.38

    # cloud attenuation, beam ratio is reduced
    bf_c = CCOEF * (cf - CRAT1)**2
    c_grad = beam * cf
    c_brad = c_grad * bf_c
    c_drad = c_grad - c_brad

    # extensive cloud attenuation, no beam
    ind = cf <= CRAT1
    c_brad[ind] = 0
    c_drad[ind] = c_grad[ind]

    # minimal cloud attenution, no beam ratio reduction
    ind = cf > CRAT2
    c_drad[ind] = diffuse[ind] * cf[ind]
    c_brad[ind] = c_grad[ind] - c_drad[ind]

    return c_grad, c_drad


def veg_beam(data, height, cosz, k):
    """
    Apply the vegetation correction to the beam irradiance
    using the equation from Links and Marks 1999

    S_b,f = S_b,o * exp[ -k h sec(theta) ] or
    S_b,f = S_b,o * exp[ -k h / cosz ]

    20150610 Scott Havens
    """

    # ensure that the sun is visible
    cosz[cosz <= 0] = 0.01

    return data * np.exp(-k * height / cosz)


def veg_diffuse(data, tau):
    """
    Apply the vegetation correction to the diffuse irradiance
    using the equation from Links and Marks 1999

    S_d,f = tau * S_d,o

    20150610 Scott Havens
    """

    return tau * data


def twostream(cosz, S0, tau=0.2, omega=0.85, g=0.3, R0=0.5):
    """
    Provides twostream solution for single-layer atmosphere over horizontal
    surface, using solution method in: Two-stream approximations to radiative
    transfer in planetary atmospheres: a unified description of existing
    methods and a new improvement, Meador & Weaver, 1980, or will use the
    delta-Eddington  method, if the -d flag is set (see: Wiscombe & Joseph
    1977).

    Args:
        cosz: The cosine of the incidence angle is cos (from program sunang).
            An error if cosz is <= 0.0; set all outputs to 0.0 and
            go on. Program will fail if incidence angle is <= 0.0, unless -0
            has been set.
        S0: The direct beam irradiance is S0 This is usually the solar
            constant for the specified wavelength band, on the specified date,
            at the top of the atmosphere, from radiation.solar.
        tau: The optical depth is tau.  0 implies an infinite optical depth.
        omega: The single-scattering albedo
        g: The asymmetry factor is g.
        R0: The reflectance of the substrate is R0.  If R0 is negative, it
            will be set to zero.

    Returns:
        R[0] - reflectance
        R[1] - transmittance
        R[2] - direct transmittance
        R[3] - upwelling irradiance
        R[4] - total irradiance at bottom
        R[5] - direct irradiance normal to beam
    """

    if cosz <= 0:
        return [0, 0, 0, 0, 0, 0]

    if S0 <= 0:
        raise ValueError('The direct beam irradiance (S0) is less than 0')

    if tau == 0:
        tau = 1e15

    if R0 < 0:
        R0 = 0

    # gamma's for phase function for all input
    gamma = mwgamma(cosz, omega, g)

    # Calcuate twostream (from libmodel/radiation/twostream.c)
    gam1 = gamma[0]
    gam2 = gamma[1]
    gam3 = gamma[2]
    gam4 = gamma[3]
    alph1 = gam1 * gam4 + gam2 * gam3
    alph2 = gam2 * gam4 + gam1 * gam3
    if gam1 < gam2:
        raise ValueError("gam1 ({}) < gam2 ({})".format(gam1, gam2))

    # (Hack - gam1 = gam2 with conservative scattering.  Need to fix this.
    # Ruh-roh...
    if gam1 == gam2:
        gam1 += 2.2204460492503131e-16

    xi = np.sqrt((gam1 - gam2) * (gam2 + gam1))
    em = np.exp(-tau * xi)
    et = np.exp(-tau / cosz)
    ep = np.exp(tau * xi)
    gpx = xi + gam1
    opx = cosz * xi + 1

    # semi-infinite?
    if (em == 0 and et == 0) or (ep >= 1e15):
        refl = omega * (gam3 * xi + alph2) / (gpx * opx)
        btrans = trans = 0

    else:

        # more intermediate variables, needed only for finite case
        omx = 1 - cosz * xi
        gmx = gam1 - xi
        rm = gam2 - gmx * R0
        rp = gam2 - gpx * R0

        # denominator for reflectance and transmittance
        denrt = ep * gpx * rm - em * gmx * rp

        # reflectance
        refl = (omega * (ep * rm * (gam3 * xi + alph2) / opx
            - em * rp * (alph2 - gam3 * xi) / omx) \
            + 2 * et * gam2 \
            * (R0 - ((alph1 * R0 - alph2) * cosz + gam4 \
            * R0 + gam3) * omega / (omx * opx)) * xi) / denrt

        # transmittance
        trans = (et * (ep * gpx * (gam2 - omega * (alph2
            - gam3 * xi) / omx) \
            - em * gmx * (gam2 - omega * (gam3 * xi + alph2) / opx)) \
            + 2 * gam2 * (alph1 * cosz + gam4) * omega * xi / \
            (omx * opx)) / denrt

        # direct transmittance
        btrans = et

        assert(refl >= 0)
        assert(trans >= 0)
        assert(btrans >= 0)
        assert(trans >= btrans * cosz)

    r = [refl,
        trans,
        btrans,
        refl * cosz * S0,
        trans * cosz * S0,
        btrans * S0]

    return r


def mwgamma(cosz, omega, g):
    """
    gamma's for phase function for input using the MEADOR WEAVER method

    Two-stream approximations to radiative transfer in planetary
    atmospheres: a unified description of existing methods and a
    new improvement, Meador & Weaver, 1980

    Args:
        cosz: cosine illumination angle
        omega: single-scattering albedo
        g: scattering asymmetry param

    Returns
        gamma values
    """

    # Meador-Weaver hybrid approx
    b0 = beta_0(cosz, g)

    # hd is denom for hybrid g1,g2
    hd = 4 * (1 - g * g * (1 - cosz))

    # these are Horner expressions corresponding to Meador-Weaver Table 1)
    if g == 1:
        g1 = g2 = (g * ((3 * (g - 1) + 4 * b0) * g - 3) + 3) / hd
    else:
        g1 = (g * (g * ((3 * g + 4 * b0) * omega - 3) - \
              3 * omega) - 4 * omega + 7) / hd

        g2 = (g * (g * ((3 * g + 4 * (b0 - 1)) * omega + 1) - \
              3 * omega) + 4 * omega - 1) / hd

    g3 = b0
    g4 = 1 - g3
    g = [g1, g2, g3, g4]
    return g


def beta_0(cosz, g):
    """
    we find the integral-sum

    sum (n=0 to inf) g^n * (2*n+1) * Pn(u0) * int (u'=0 to 1) Pn(u')

    note that int of Pn vanishes for even values of n (Abramowitz &
    Stegun, eq 22.13.8-9); therefore the series becomes

    sum (n=0 to inf) g^n * (2*n+1) * Pn(u0) * f(m)

    where 2*m+1 = n and the f's are computed recursively

    Args:
        cosz: cosine illumination angle
        g: scattering asymmetry param

    Returns:
        beta_0

    """

    MAXNO = 2048
    TOL = 1e-9

    assert(cosz > 0 and cosz <= 1)
    assert(g >= 0 and g <= 1)

    # Legendre polynomials of degree 0 and 1

    pnm2 = 1
    pnm1 = cosz

    # first coefficients and initial sum
    fm = -1/8
    gn = 7 * g * g * g
    the_sum = 3 * g * cosz / 2

    # sum until convergence; we use the even terms only for the recursive
    # calculation of the Legendre polynomials
    if (g != 0 and cosz != 0):
        for n in range(2, MAXNO):

            # order n Legendre polynomial
            pn = ((2 * n - 1) * cosz * pnm1 + (1 - n) * pnm2) / n

            # even terms vanish
            if (n % 2) == 1:
                last = the_sum
                the_sum = last + gn * fm * pn
                if (np.abs((the_sum - last) / the_sum) < TOL and the_sum <= 1):
                    break

                # recursively find next f(m) and gn coefficients
                # n = 2 * m + 1
                m = (n - 1) / 2
                fm *= -(2 * m + 1) / (2 * (m + 2))
                gn *= g * g * (4 * m + 7) / (4 * m + 3)

            # ready to compute next Legendre polynomial
            pnm2 = pnm1
            pnm1 = pn

        # warn if no convergence
        if n == MAXNO:
            print("%s: %s - cosz=%g g=%g sum=%g last=%g fm=%g",
                  "betanaught", "no convergence",
                    cosz, g, the_sum, last, fm)
            if the_sum > 1:
                the_sum = 1

        else:
            assert(the_sum >= 0 and the_sum <= 1)

    else:
        the_sum = 0

    return (1 - the_sum) / 2


def solar(d, w=[0.28, 2.8]):
    """
    Solar calculates exoatmospheric direct solar irradiance.  If two arguments
    to -w are given, the integral of solar irradiance over the range will be
    calculated.  If one argument is given, the spectral irradiance will be
    calculated.

    If no wavelengths are specified on the command line, single wavelengths in
    um will be read from the standard input and the spectral irradiance
    calculated for each.

    Args:
        w - [um um2] If  two  arguments  are  given, the integral of solar
            irradiance in the range um to um2 will be calculated.  If one
            argument is given, the spectral irradiance will be calculated.
        d - date object, This is used to calculate the solar radius vector
            which divides the result

    Returns:
        s - direct solar irradiance
    """

    if len(w) != 2:
        raise ValueError('length of w must be 2')

    # Adjust date time for solar noon
    d = d.replace(hour=12, minute=0, second=0)

    # Calculate the ephemeris parameters
    declination, omega, rad_vec = sunang.ephemeris(d)

    # integral over a wavelength range
    s = solint(w[0], w[1]) / rad_vec ** 2

    return s


def solint(a, b):
    """
    integral of solar constant from wavelengths a to b in micometers

    This uses scipy functions which will produce different results
    from the IPW equvialents of 'akcoef' and 'splint'
    """

    # Solar data
    data = solar_data()

    wave = data[:, 0]
    val = data[:, 1]

    # calcualte splines
    c = Akima1DInterpolator(wave, val)

    # Take the integral between the two wavelengths
    intgrl, ierror = quad(c, a, b, limit=120)

    return intgrl * SOLAR_CONSTANT


def model_solar(dt, lat, lon, tau=0.2, tzone=0):
    """
    Model solar radiation at a point
    Combines sun angle, solar and two stream

    Args:
        dt - datetime object
        lat - latitude
        lon - longitude
        tau - optical depth
        tzone - time zone

    Returns:
        corrected solar radiation
    """

    # determine the sun angle
    cosz, az, rad_vec = sunang.sunang(dt, lat, lon)

    # calculate the solar irradiance
    sol = solar(dt, [0.28, 2.8])

    # calculate the two stream model value
    R = twostream(cosz, sol, tau=tau)

    return R[4]


def get_hrrr_cloud(df_solar, df_meta, logger, lat, lon):
    """
    Take the combined solar from HRRR and use the two stream calculation
    at the specific HRRR pixels to find the cloud_factor.

    Args:
        df_solar - solar dataframe from hrrr
        df_meta - meta_data from hrrr
        logger - smrf logger
        lat - basin lat
        lon - basin lon

    Returns:
        df_cf - cloud factor dataframe in same format as df_solar input
    """

    # get and loop through the columns
    clms = df_solar.columns
    dates = df_solar.index.values[:]

    # find each cell solar at top of atmosphere for each date
    basin_sol = df_solar.copy()
    for idt, dt in enumerate(dates):
        # get solar using twostream
        dtt = pd.to_datetime(dt)
        basin_sol.iloc[idt, :] =  model_solar(dtt, lat, lon)

    # if it's close to sun down or sun up, then the cloud factor gets difficult to calculate
    basin_sol[basin_sol < 50] = 0
    df_solar[basin_sol < 50] = 0

    # This would be the proper way to do this but it's too computationally expensive
    # cs_solar = df_solar.copy()
    # for dt, row in cs_solar.iterrows():
    #     dtt = pd.to_datetime(dt)
    #     for ix,value in row.iteritems():
    #         # get solar using twostream only if the sun is up
    #         if value > 0:
    #             cs_solar.loc[dt, ix] = model_solar(dtt, df_meta.loc[ix, 'latitude'], df_meta.loc[ix, 'longitude'])

    # This will produce NaN values when the sun is down
    df_cf = df_solar / basin_sol

    # linear interpolate the NaN values at night
    df_cf = df_cf.interpolate(method='linear').ffill()

    # Clean up the dataframe to be between 0 and 1
    df_cf[df_cf > 1.0] = 1.0
    df_cf[df_cf < 0.0] = 0.0



    # # create cloud factor dataframe
    # df_cf = df_solar.copy()
    # #df_basin_sol = pd.DataFrame(index = dates, data = basin_sol)

    # # calculate cloud factor from basin solar
    # for cl in clms:
    #     cf_tmp = df_cf[cl].values[:]/basin_sol
    #     cf_tmp[np.isnan(cf_tmp)] = 0.0
    #     cf_tmp[cf_tmp > 1.0] = 1.0
    #     df_cf[cl] = cf_tmp

    # df_cf = df_solar.divide(df_basin_sol)
    # # clip to 1.0
    # df_cf = df_cf.clip(upper=1.0)
    # # fill nighttime with 0
    # df_cf = df_cf.fillna(value=0.0)

    # for idc, cl in enumerate(clms):
    #     # get lat and lon for each hrrr pixel
    #     lat = df_meta.loc[ cl,'latitude']
    #     lon = df_meta.loc[ cl,'longitude']
    #
    #     # get solar values and make empty cf vector
    #     sol_vals = df_solar[cl].values[:]
    #     cf_vals = np.zeros_like(sol_vals)
    #     cf_vals[:] = np.nan
    #
    #     # loop through time series for the pixel
    #     for idt, sol in enumerate(sol_vals):
    #         dt = pd.to_datetime(dates[idt])
    #         # get the modeled solar
    #         calc_sol = model_solar(dt, lat, lon)
    #         if calc_sol == 0.0:
    #             cf_tmp = 0.0
    #             # diff = sol - calc_sol
    #             # if diff > 5:
    #             #     print(sol)
    #         else:
    #             cf_tmp = sol / calc_sol
    #         if cf_tmp > 1.0:
    #             logger.warning('CF to large: ')
    #             logger.warning('{} for {} at {}'.format(cf_tmp, cl, idt))
    #             cf_tmp = 1.0
    #         # store value
    #         cf_vals[idt] =cf_tmp
    #
    #     # store pixel cloud factor
    #     df_cf[cl] = cf_vals

    return df_cf


def solar_data():
    """
    Solar data from Thekaekara, NASA TR-R-351, 1979
    """

    return np.array([[0.00e+0, 0.0000000000000000e+0],
                     [1.20e-1, 7.2064702602003287e-5],
                     [1.40e-1, 2.1619410780600986e-5],
        [1.50e-1, 5.0445291821402301e-5],
        [1.60e-1, 1.6574881598460755e-4],
        [1.70e-1, 4.5400762639262068e-4],
        [1.80e-1, 9.0080878252504105e-4],
        [1.90e-1, 1.9529534405142891e-3],
        [2.00e-1, 7.7109231784143517e-3],
        [2.10e-1, 1.6502816895858752e-2],
        [2.20e-1, 4.1437203996151890e-2],
        [2.25e-1, 4.6769991988700132e-2],
        [2.30e-1, 4.8067156635536191e-2],
        [2.35e-1, 4.2734368642987949e-2],
        [2.40e-1, 4.5400762639262071e-2],
        [2.45e-1, 5.2102779981248376e-2],
        [2.50e-1, 5.0733550631810313e-2],
        [2.55e-1, 7.4947290706083422e-2],
        [2.60e-1, 9.3684113382604272e-2],
        [2.65e-1, 1.3331969981370607e-1],
        [2.70e-1, 1.6719011003664763e-1],
        [2.75e-1, 1.4701199330808671e-1],
        [2.80e-1, 1.5998363977644729e-1],
        [2.85e-1, 2.2700381319631035e-1],
        [2.90e-1, 3.4735186654165584e-1],
        [2.95e-1, 4.2085786319569921e-1],
        [3.00e-1, 3.7041257137429690e-1],
        [3.05e-1, 4.3455015669007980e-1],
        [3.10e-1, 4.9652580092780263e-1],
        [3.15e-1, 5.5057432787930508e-1],
        [3.20e-1, 5.9813703159662727e-1],
        [3.25e-1, 7.0263085036953205e-1],
        [3.30e-1, 7.6316520055521482e-1],
        [3.35e-1, 7.7901943512765555e-1],
        [3.40e-1, 7.7397490594551530e-1],
        [3.45e-1, 7.7037167081541515e-1],
        [3.50e-1, 7.8766719943989590e-1],
        [3.55e-1, 7.8046072917969557e-1],
        [3.60e-1, 7.6965102378939508e-1],
        [3.65e-1, 8.1577243345467720e-1],
        [3.70e-1, 8.5108413772965880e-1],
        [3.75e-1, 8.3378860910517805e-1],
        [3.80e-1, 8.0712466914243679e-1],
        [3.85e-1, 7.9127043456999609e-1],
        [3.90e-1, 7.9127043456999609e-1],
        [3.95e-1, 8.5684931393781909e-1],
        [4.00e-1, 1.0298046001826270e+0],
        [4.05e-1, 1.1847437107769340e+0],
        [4.10e-1, 1.2618529425610776e+0],
        [4.15e-1, 1.2784278241595383e+0],
        [4.20e-1, 1.2589703544569974e+0],
        [4.25e-1, 1.2200554150519156e+0],
        [4.30e-1, 1.1811404756468339e+0],
        [4.35e-1, 1.1984360042713147e+0],
        [4.40e-1, 1.3043711170962595e+0],
        [4.45e-1, 1.3850835840105032e+0],
        [4.50e-1, 1.4456179341961859e+0],
        [4.55e-1, 1.4823709325232076e+0],
        [4.60e-1, 1.4888567557573879e+0],
        [4.65e-1, 1.4758851092890273e+0],
        [4.70e-1, 1.4650754038987267e+0],
        [4.75e-1, 1.4730025211849472e+0],
        [4.80e-1, 1.4946219319655481e+0],
        [4.85e-1, 1.4239985234155849e+0],
        [4.90e-1, 1.4052617007390641e+0],
        [4.95e-1, 1.4124681709992644e+0],
        [5.00e-1, 1.3994965245309039e+0],
        [5.05e-1, 1.3836422899584631e+0],
        [5.10e-1, 1.3562577029697018e+0],
        [5.15e-1, 1.3209459986947202e+0],
        [5.20e-1, 1.3209459986947202e+0],
        [5.25e-1, 1.3346382921891008e+0],
        [5.30e-1, 1.3274318219289006e+0],
        [5.35e-1, 1.3101362933044197e+0],
        [5.40e-1, 1.2849136473937186e+0],
        [5.45e-1, 1.2640148836391377e+0],
        [5.50e-1, 1.2431161198845568e+0],
        [5.55e-1, 1.2395128847544565e+0],
        [5.60e-1, 1.2214967091039557e+0],
        [5.65e-1, 1.2287031793641560e+0],
        [5.70e-1, 1.2337477085462963e+0],
        [5.75e-1, 1.2387922377284365e+0],
        [5.80e-1, 1.2359096496243563e+0],
        [5.85e-1, 1.2337477085462963e+0],
        [5.90e-1, 1.2250999442340559e+0],
        [5.95e-1, 1.2121282977656953e+0],
        [6.00e-1, 1.2005979453493748e+0],
        [6.05e-1, 1.1869056518549941e+0],
        [6.10e-1, 1.1782578875427537e+0],
        [6.20e-1, 1.1544765356840926e+0],
        [6.30e-1, 1.1314158308514516e+0],
        [6.40e-1, 1.1126790081749307e+0],
        [6.50e-1, 1.0888976563162696e+0],
        [6.60e-1, 1.0708814806657688e+0],
        [6.70e-1, 1.0492620698851678e+0],
        [6.80e-1, 1.0283633061305869e+0],
        [6.90e-1, 1.0103471304800861e+0],
        [7.00e-1, 9.8656577862142496e-1],
        [7.10e-1, 9.6854960297092417e-1],
        [7.20e-1, 9.4693019219032319e-1],
        [7.30e-1, 9.2963466356584240e-1],
        [7.40e-1, 9.0801525278524139e-1],
        [7.50e-1, 8.8999907713474059e-1],
        [8.00e-1, 7.9775625780417640e-1],
        [8.50e-1, 7.1199926170779244e-1],
        [9.00e-1, 6.4065520613180922e-1],
        [9.50e-1, 6.0174026672672744e-1],
        [1.00e+0, 5.3760268141094450e-1],
        [1.10e+0, 4.2662303940385946e-1],
        [1.20e+0, 3.4879316059369590e-1],
        [1.30e+0, 2.8537622230393302e-1],
        [1.40e+0, 2.4213740074273104e-1],
        [1.50e+0, 2.0682569646774943e-1],
        [1.60e+0, 1.7583787434888801e-1],
        [1.70e+0, 1.4557069925604664e-1],
        [1.80e+0, 1.1458287713718522e-1],
        [1.90e+0, 9.0801525278524142e-2],
        [2.00e+0, 7.4226643680063386e-2],
        [2.10e+0, 6.4858232341802959e-2],
        [2.20e+0, 5.6931115055582595e-2],
        [2.30e+0, 4.9003997769362232e-2],
        [2.40e+0, 4.6121409665282103e-2],
        [2.50e+0, 3.8914939405081775e-2],
        [2.60e+0, 3.4591057248961578e-2],
        [2.70e+0, 3.0987822118861412e-2],
        [2.80e+0, 2.8105234014781281e-2],
        [2.90e+0, 2.5222645910701150e-2],
        [3.00e+0, 2.2340057806621019e-2],
        [3.10e+0, 1.8736822676520856e-2],
        [3.20e+0, 1.6286622788052742e-2],
        [3.30e+0, 1.3836422899584630e-2],
        [3.40e+0, 1.1962740631932545e-2],
        [3.50e+0, 1.0521446579892480e-2],
        [3.60e+0, 9.7287348512704438e-3],
        [3.70e+0, 8.8639584200464042e-3],
        [3.80e+0, 7.9991819888223649e-3],
        [3.90e+0, 7.4226643680063384e-3],
        [4.00e+0, 6.8461467471903120e-3],
        [4.10e+0, 6.2696291263742857e-3],
        [4.20e+0, 5.6210468029562563e-3],
        [4.30e+0, 5.1165938847422333e-3],
        [4.40e+0, 4.6842056691302139e-3],
        [4.50e+0, 4.2518174535181938e-3],
        [4.60e+0, 3.8194292379061740e-3],
        [4.70e+0, 3.4591057248961576e-3],
        [4.80e+0, 3.2429116170901479e-3],
        [4.90e+0, 2.9546528066821346e-3],
        [5.00e+0, 2.7600781096567258e-3],
        [6.00e+0, 1.2611322955350576e-3],
        [7.00e+0, 7.1344055575983254e-4],
        [8.00e+0, 4.3238821561201970e-4],
        [9.00e+0, 2.7384586988761247e-4],
        [1.00e+1, 1.8016175650500822e-4],
        [1.10e+1, 1.2250999442340559e-4],
        [1.20e+1, 8.6477643122403945e-5],
        [1.30e+1, 6.2696291263742856e-5],
        [1.40e+1, 3.9635586431101808e-5],
        [1.50e+1, 3.5311704274981611e-5],
        [1.60e+1, 2.7384586988761248e-5],
        [1.70e+1, 2.2340057806621018e-5],
        [1.80e+1, 1.7295528624480788e-5],
        [1.90e+1, 1.4412940520400656e-5],
        [2.00e+1, 1.1530352416320527e-5],
        [2.50e+1, 4.3959468587222005e-6],
        [3.00e+1, 2.1619410780600985e-6],
        [3.50e+1, 1.1530352416320526e-6],
        [4.00e+1, 6.7740820445883089e-7],
        [5.00e+1, 2.7384586988761249e-7],
        [6.00e+1, 1.3692293494380625e-7],
        [8.00e+1, 5.0445291821402299e-8],
        [1.00e+2, 2.1619410780600986e-8],
        [1.00e+3, 0.0000000000000000e+0]])

#####################################################################
# IPW function
#####################################################################


def sunang_ipw(date, lat, lon, zone=0, slope=0, aspect=0):
    """
    Wrapper for the IPW sunang function

    Args:
        date - date to calculate sun angle for (datetime object)
        lat - latitude in decimal degrees
        lon - longitude in decimal degrees
        zone - The  time  values  are  in the time zone which is min minutes
            west of Greenwich (default: 0).  For example, if input times are
            in Pacific Standard Time, then min would be 480.
        slope (default=0) - slope of surface
        aspect (default=0) - aspect of surface

    Returns:
        cosz - cosine of the zeinith angle
        azimuth - solar azimuth

    Created April 17, 2015
    Scott Havens
    """

    # date string
    dstr = date.strftime('%Y,%m,%d,%H,%M,%S')

    # degree strings
    d, m, sd = deg_to_dms(lat)
    lat_str = str(d) + ',' + str(m) + ',' + '%02.1i' % sd

    d, m, sd = deg_to_dms(lon)
    lon_str = str(d) + ',' + str(m) + ',' + '%02.1i' % sd

    # prepare the command
    cmd_str = 'sunang -b %s -l %s -t %s -s %i -a %i -z %i' % \
        (lat_str, lon_str, dstr, slope, aspect, zone)

    out = sp.check_output([cmd_str], shell=True, universal_newlines=True)

    c = out.rstrip().split(' ')

    cosz = float(c[1])
    azimuth = float(c[3])

    return cosz, azimuth


# def sunang_thread(queue, date, lat, lon, zone=0, slope=0, aspect=0):
#     """
#     See sunang for input descriptions

#     Args:
#         queue: queue with cosz, azimuth
#         date: loop through dates to accesss queue, must be same as rest of queues

#     20160325 Scott Havens
#     """

#     if 'cosz' not in queue.keys():
#         raise ValueError('queue must have cosz key')
#     if 'azimuth' not in queue.keys():
#         raise ValueError('queue must have cosz key')

#     log = logging.getLogger(__name__)

#     for t in date:

#         log.debug('%s Calculating sun angle' % t)

#         cosz, azimuth = sunang(t.astimezone(pytz.utc), lat, lon,
#                                zone, slope, aspect)

#         queue['cosz'].put([t, cosz])
#         queue['azimuth'].put([t, azimuth])

def solar_ipw(d, w=[0.28, 2.8]):
    """
    Wrapper for the IPW solar function

    Solar calculates exoatmospheric direct solar irradiance.  If two arguments
    to -w are given, the integral of solar irradiance over the range will be
    calculated.  If one argument is given, the spectral irradiance will be
    calculated.

    If no wavelengths are specified on the command line, single wavelengths in
    um will be read from the standard input and the spectral irradiance
    calculated for each.

    Args:
        w - [um um2] If  two  arguments  are  given, the integral of solar
            irradiance in the range um to um2 will be calculated.  If one
            argument is given, the spectral irradiance will be calculated.
        d - date object, This is used to calculate the solar radius vector
            which divides the result

    Returns:
        s - direct solar irradiance

    20151002 Scott Havens
    """

    # date string
    dstr = d.strftime('%Y,%m,%d')

    # wavelength string
    if (len(w) > 1):
        w = ','.join(str(x) for x in w)

    cmd_str = 'solar -w %s -d %s -a' % (w, dstr)

    # p = sp.Popen(cmd_str, stdout=sp.PIPE, shell=True, env={"PATH": IPW})
    out = sp.check_output([cmd_str], shell=True, universal_newlines=True)
    # get the results
    # out, err = p.communicate()

    return float(out.rstrip())


def twostream_ipw(mu0, S0, tau=0.2, omega=0.85, g=0.3, R0=0.5, d=False):
    """
    Wrapper for the twostream.c IPW function

    Provides twostream solution for single-layer atmosphere over horizontal
    surface, using solution method in: Two-stream approximations to radiative
    transfer in planetary atmospheres: a unified description of existing
    methods and a new improvement, Meador & Weaver, 1980, or will use the
    delta-Eddington  method, if the -d flag is set (see: Wiscombe & Joseph
    1977).

    Args:
        mu0 - The cosine of the incidence angle is cos (from program sunang).
        0 - Do not force an error if mu0 is <= 0.0; set all outputs to 0.0 and
            go on. Program will fail if incidence angle is <= 0.0, unless -0
            has been set.
        tau - The optical depth is tau.  0 implies an infinite optical depth.
        omega - The single-scattering albedo is omega.
        g - The asymmetry factor is g.
        R0 - The reflectance of the substrate is R0.  If R0 is negative, it
            will be set to zero.
        S0 - The direct beam irradiance is S0 This is usually the solar
            constant for the specified wavelength band, on the specified date,
            at the top of the atmosphere, from program solar. If S0 is
            negative, it will be set to 1/cos, or 1 if cos is not specified.
        d - The delta-Eddington method will be used.

    Returns:
        R[0] - reflectance
        R[1] - transmittance
        R[2] - direct transmittance
        R[3] - upwelling irradiance
        R[4] - total irradiance at bottom
        R[5] - direct irradiance normal to beam

    20151002 Scott Havens
    """

    # prepare the command
    dflag = ''
    if d:
        dflag = '-d'

    cmd_str = 'twostream -u %s -0 -t %s -w %s -g %s -r %s -s %s %s' % \
        (str(mu0), str(tau), str(omega), str(g), str(R0), str(S0), dflag)

    out = sp.check_output([cmd_str], shell=True, universal_newlines=True)

    c = out.rstrip().split('\n')

    R = np.ndarray((6, 1))
    for i, m in enumerate(c):
        R[i] = float(m.rstrip().split(' ')[-1])

    return R
