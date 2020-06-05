import logging
import warnings

import numpy as np
import pandas as pd
from scipy.integrate import quad, IntegrationWarning
from scipy.interpolate import Akima1DInterpolator
from topocalc.shade import shade

from smrf.envphys import sunang


# define some constants
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


def shade_thread(queue, date, sin_slope, aspect, zenith=None):
    """
    See shade for input argument descriptions

    Args:
        queue: queue with illum_ang, cosz, azimuth
        date_time: loop through dates to accesss
        sin_slope: numpy array of sine of slope angles sin(S)
        aspect: numpy array of aspect in radians from south
        azimuth: azimuth in degrees to the sun -180..180 (comes from sunang)
        zenith: the solar zenith angle 0..90 degrees

    """

    for v in ['cosz', 'azimuth', 'illum_ang']:
        if v not in queue.keys():
            raise ValueError('Queue must have {} key'.format(v))

    log = logging.getLogger(__name__)

    for t in date:

        log.debug('%s Calculating illumination angle' % t)

        mu = None
        cosz = queue['cosz'].get(t)

        if cosz > 0:
            azimuth = queue['azimuth'].get(t)
            mu = shade(sin_slope, aspect, azimuth, cosz, zenith)

        queue['illum_ang'].put([t, mu])


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
                         - em * rp * (alph2 - gam3 * xi) / omx)
                + 2 * et * gam2
                * (R0 - ((alph1 * R0 - alph2) * cosz + gam4
                         * R0 + gam3) * omega / (omx * opx)) * xi) / denrt

        # transmittance
        trans = (et * (ep * gpx * (gam2 - omega * (alph2
                                                   - gam3 * xi) / omx)
                       - em * gmx * (gam2 - omega * (gam3 * xi + alph2) / opx))
                 + 2 * gam2 * (alph1 * cosz + gam4) * omega * xi /
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
        g1 = (g * (g * ((3 * g + 4 * b0) * omega - 3) -
                   3 * omega) - 4 * omega + 7) / hd

        g2 = (g * (g * ((3 * g + 4 * (b0 - 1)) * omega + 1) -
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

    # calculate splines
    c = Akima1DInterpolator(wave, val)

    with warnings.catch_warnings(record=True) as messages:
        warnings.simplefilter('always', category=IntegrationWarning)
        # Take the integral between the two wavelengths
        intgrl, ierror = quad(c, a, b, limit=120)

        log = logging.getLogger(__name__)
        for warning in messages:
            log.warning(warning.message)

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
    dates = df_solar.index.values[:]

    # find each cell solar at top of atmosphere for each date
    basin_sol = df_solar.copy()
    for idt, dt in enumerate(dates):
        # get solar using twostream
        dtt = pd.to_datetime(dt)
        basin_sol.iloc[idt, :] = model_solar(dtt, lat, lon)

    # if it's close to sun down or sun up, then the cloud factor gets
    # difficult to calculate
    basin_sol[basin_sol < 50] = 0
    df_solar[basin_sol < 50] = 0

    # This would be the proper way to do this but it's too
    # computationally expensive
    # cs_solar = df_solar.copy()
    # for dt, row in cs_solar.iterrows():
    #     dtt = pd.to_datetime(dt)
    #     for ix,value in row.iteritems():
    #         # get solar using twostream only if the sun is
    # up
    #         if value > 0:
    #             cs_solar.loc[dt, ix] = model_solar(dtt,
    # df_meta.loc[ix, 'latitude'], df_meta.loc[ix, 'longitude'])

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
