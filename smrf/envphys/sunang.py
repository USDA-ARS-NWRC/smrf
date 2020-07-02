import logging
from math import asin, atan, cos, fmod, sin, sqrt, tan

import numpy as np
import pytz

JULIAN_CENTURY = 36525		# days in Julian century
DEGS_IN_CIRCLE = 3.6e2        # degrees in circle
TOLERANCE = 1.1920928955e-07
M_PI = 3.14159265358979323846
M_PI_2 = 2 * M_PI
MAX_DECLINATION = 23.6


def sunang(date_time, latitude, longitude, truncate=True):
    """
    Calculate the sun angle (the azimuth and zenith angles of
    the sun's position) for a given geodetic location for a single
    date time and coordinates. The function can take either latitude
    longitude position as a single point or numpy array.

    Args:
        date_time: python datetime object
        latitude: value or np.ndarray (in degrees)
        longitude: value or np.ndarray (in degrees)
        truncate: True will replicate the IPW output precision, not
                applied if position is an array

    Returns
        cosz - cosine of the zenith angle, same shape as input position
        azimuth - solar azimuth, same shape as input position
        rad_vec - Earth-Sun radius vector

    """

    # Calculate the ephemeris parameters
    declination, omega, rad_vec = ephemeris(date_time)

    # calculate the sun angle
    rad_latitude = latitude * M_PI / 180
    rad_longitude = longitude * M_PI / 180
    mu, azimuth = sunpath(rad_latitude, rad_longitude, declination, omega)

    azimuth = azimuth * 180 / M_PI

    if truncate and not isinstance(mu, np.ndarray):
        mu = float('{0:.6f}'.format(mu))
        azimuth = float('{0:.5g}'.format(azimuth))
        rad_vec = float('{0:.5g}'.format(rad_vec))

    return mu, azimuth, rad_vec


def sunang_thread(queue, date, lat, lon):
    """
    See sunang for input descriptions

    Args:
        queue: queue with cosz, azimuth
        date: loop through dates to accesss queue, must be same as
                rest of queues

    """

    if 'cosz' not in queue.keys():
        raise ValueError('queue must have cosz key')
    if 'azimuth' not in queue.keys():
        raise ValueError('queue must have cosz key')

    log = logging.getLogger(__name__)

    for t in date:

        log.debug('%s Calculating sun angle' % t)

        cosz, azimuth, rad_vec = sunang(t.astimezone(pytz.utc), lat, lon)

        queue['cosz'].put([t, cosz])
        queue['azimuth'].put([t, azimuth])


def sunpath(latitude, longitude, declination, omega):
    """
    Sun angle from solar declination and longtitude

    Args:
        latitude: in radians
        longitude: in radians
        declination: solar declination (radians)
        omega: solar longitude (radians)

    Returns
        cosz: cosine of solar zenith
        azimuth: solar azimuth in radians
    """

    if isinstance(latitude, np.ndarray):
        if np.any(np.abs(latitude) > M_PI_2):
            raise ValueError("latitude array not between -90 and +90 degrees")

        if np.any(np.abs(longitude) > M_PI):
            raise ValueError(
                "longitude array not between -180 and +180 degrees")

    else:
        if np.abs(latitude) > M_PI_2:
            raise ValueError(
                "latitude ({} deg) not between -90 and +90 degrees".format(
                    latitude*180/M_PI))

        if np.abs(longitude) > M_PI:
            raise ValueError(
                "longitude ({} deg) not between -180 and +180 degrees".format(
                    longitude*180/M_PI))

    if np.abs(declination) > M_PI*MAX_DECLINATION/180:
        raise ValueError(
            "declination ({} deg) > maximum declination ({} deg)".format(
                declination*180/M_PI, MAX_DECLINATION))

    if np.abs(omega) > M_PI:
        raise ValueError(
            """longitude of sun ({} deg) not between -180 and """
            """+180 degrees""".format(omega*180/M_PI))

    cosz, az = rotate(np.sin(declination), omega, np.sin(latitude), longitude)

    return cosz, az


def dsign(a, b):
    """
    modified from /usr/src/lib/libF77/d_sign.c
    """

    x = a if a >= 0 else -a
    y = x if b >= 0 else -x
    return y

# original ibm 360/44 fortran ivf - vislab - wilson - 29jul79
# translated, modified and reduced by dozier - ucsb - 11/81


def ephemeris(dt):
    """
    Calculates radius vector, declination, and apparent longitude
    of sun, as function of the given date and time.

    The routine is adapted from:

    W. H. Wilson, Solar ephemeris algorithm, Reference 80-13, 70
        pp., Scripps Institution of Oceanography, University of
        California, San Diego, La Jolla, CA, 1980.

    Args:
        dt: date time python object

    Returns:
        declin: solar declination angle, in radians
        omega: sun longitude, in radians
        r: Earth-Sun radius vector

    """

    one = 1.0
    degrd = atan(one) / 45.0

    # Convert time to seconds since midnight
    gmts = 3600.0 * dt.hour + 60.0 * dt.minute + dt.second

    # p51 = gmts/3600/24*360

    # The int() is required for compatability with IPW as the divide by
    # 100 keeps the value as an integer where python converts to a float...
    p51 = gmts / 10.0 / 24.0
    p22 = int(((dt.year - 1900) * JULIAN_CENTURY - 25) / 100) + \
        yearday(dt.year, dt.month, dt.day) - 0.5
    p23 = (p51 / DEGS_IN_CIRCLE + p22) / JULIAN_CENTURY
    p22 = p23 * JULIAN_CENTURY

    # mean longitude - p24
    p11 = 279.69668
    p12 = 0.9856473354
    p13 = 3.03e-4
    p24 = p11 + fmod(p12 * p22, DEGS_IN_CIRCLE) + p13 * p23 * p23
    p24 = fmod(p24, DEGS_IN_CIRCLE)

    # mean anomaly - p25
    p11 = 358.47583
    p12 = 0.985600267
    p13 = -1.5e-4
    p14 = -3.e-6
    p25 = p11 + fmod(p12 * p22, DEGS_IN_CIRCLE) + p23 * p23 * (p13 + p14 * p23)
    p25 = fmod(p25, DEGS_IN_CIRCLE)

    # eccentricity - p26
    p11 = 0.01675104
    p12 = -4.18e-5
    p13 = -1.26e-7
    p26 = p11 + p23 * (p12 + p13 * p23)
    p11 = p25 * degrd
    p12 = p11

    while True:
        p13 = p12
        p12 = p11 + p26 * sin(p13)
        if abs((p12 - p13) / p12) < TOLERANCE:
            break

    p13 = p12 / degrd

    # true anomaly - p27`
    p27 = 2.0 * atan(sqrt((1.0 + p26) / (1.0 - p26))
                     * tan(p13 / 2.0 * degrd)) / degrd
    if dsign(1.0, p27) != dsign(1.0, sin(p13 * degrd)):
        p27 += 1.8e2
    if p27 < 0.0:
        p27 += DEGS_IN_CIRCLE

    # radius vector - r
    r = 1.0 - p26 * cos(p13 * degrd)

    # aberration - p29
    p29 = -20.47 / r / 3600

    # mean obliquity - p43
    p11 = 23.452294
    p12 = -0.0130125
    p13 = -1.64e-6
    p14 = 5.03e-7
    p43 = p11 + p23 * (p12 + p23 * (p13 + p14 * p23))

    #  mean ascension - p45
    p11 = 279.6909832
    p12 = 0.98564734
    p13 = 3.8707
    p13 = 3.8708e-4
    p45 = p11 + fmod(p12 * p22, DEGS_IN_CIRCLE) + p13 * p23 * p23
    p45 = fmod(p45, DEGS_IN_CIRCLE)

    # nutation and longitude pert
    p11 = 296.104608
    p12 = 1325 * DEGS_IN_CIRCLE
    p13 = 198.8491083
    p14 = 0.00919167
    p15 = 1.4388e-5
    p28 = p11 + fmod(p12 * p23, DEGS_IN_CIRCLE) + p23 * \
        (p13 + p23 * (p14 + p15 * p23))
    p28 = fmod(p28, DEGS_IN_CIRCLE)

    # mean elongation of moon - p30
    p11 = 350.737486
    p12 = 1236 * DEGS_IN_CIRCLE
    p13 = 307.1142167
    p14 = 1.436e-3
    p30 = p11 + fmod(p12 * p23, DEGS_IN_CIRCLE) + p23 * (p13 + p14 * p23)
    p30 = fmod(p30, DEGS_IN_CIRCLE)

    # moon long of ascending node - p31
    p11 = 259.183275
    p12 = -5 * DEGS_IN_CIRCLE
    p13 = -134.142008
    p14 = 2.0778e-3
    p31 = p11 + fmod(p12 * p23, DEGS_IN_CIRCLE) + p23 * (p13 + p14 * p23)
    p31 = fmod(p31, DEGS_IN_CIRCLE)

    # mean long of moon - p31
    p11 = 270.434164
    p12 = 1336 * DEGS_IN_CIRCLE
    p13 = 307.8831417
    p14 = -1.1333e-3
    p32 = p11 + fmod(p12 * p23, DEGS_IN_CIRCLE) + p23 * (p13 + p14 * p23)
    p32 = fmod(p32, DEGS_IN_CIRCLE)

    # moon perturbation of sun long - p33
    p33 = 6.454 * sin(p30 * degrd) + 0.013 * sin(3 * p30 * degrd) + \
        0.177 * sin((p30 + p28) * degrd) - \
        0.424 * sin((p30 - p28) * degrd)
    p33 = p33 / 3600

    # nutation of long - p34
    p34 = -(17.234 - 0.017 * p23) * sin(p31 * degrd) + \
        0.209 * sin(2 * p31 * degrd) - \
        0.204 * sin(2 * p32 * degrd)
    p34 = p34 - 1.257 * sin(2 * p24 * degrd) + 0.127 * sin(p28 * degrd)
    p34 = p34 / 3600

    # nutation in obliquity - p34
    p35 = 9.214 * cos(p31 * degrd) + 0.546 * cos(2 * p24 * degrd) - \
        .09 * cos(2 * p31 * degrd) + 0.088 * cos(2 * p32 * degrd)
    p35 = p35 / 3600

    # inequalities of long period - p36
    p36 = 0.266 * sin((31.8 + 119 * p23) * degrd) + \
        ((1.882 - 0.016 * p23) * degrd) * \
        sin((57.24 + 150.27 * p23) * degrd)
    p36 = p36 + 0.202 * sin((315.6 + 893.3 * p23) * degrd) + \
        1.089 * p23 * p23 + 6.4 * sin((231.19 + 20.2 * p23) * degrd)
    p36 = p36 / 3600

    # apparent longitude - p41
    p41 = p27 - p25 + p24 + p29 + p33 + p36 + p34

    p43 += p35

    # apparent right ascension - p44
    p44 = atan(tan(p41 * degrd) * cos(p43 * degrd)) / degrd
    if dsign(one, p44) != dsign(one, sin(p41 * degrd)):
        p44 += 1.8e2
    if p44 < 0:
        p44 += DEGS_IN_CIRCLE

    # equation of time - p46
    p46 = p45 - p44
    if p46 > 1.8e2:
        p46 -= DEGS_IN_CIRCLE

    # declination - p47
    p47 = asin(sin(p41 * degrd) * sin(p43 * degrd))
    declin = p47

    # hour angle in degrees - p48
    p48 = p51 + p46 - 1.8e2
    if p48 > 180:
        p48 -= DEGS_IN_CIRCLE
    elif p48 < -180:
        p48 += DEGS_IN_CIRCLE
    omega = -p48 * degrd

    return declin, omega, r


def rotate(mu, azm, mu_r, lam_r):
    """
    Calculates new spherical coordinates if system rotated about
    origin.  Coordinates are right-hand system.  All angles are in
    radians.

    Args:
        mu: cosine of angle theta from z-axis in old coordinate
            system, sin(declination)
        azm: azimuth (+ccw from x-axis) in old coordinate system,
            hour angle of sun (long. where sun is vertical)
        mu_r: cosine of angle theta_r of rotation of z-axis, sin(latitude)
        lam_r: azimuth (+ccw) of rotation of x-axis, longitude

    Returns:
        muPrime: cosine of the solar zenith
        aPrime: solar azimuth in radians
    """

    # Check input values: mu = cos(theta) mu_r = cos(theta-sub-r)
    if mu < -1.0 or mu > 1.0:
        raise ValueError(
            "rotate: mu = cos(theta) = {} is not between -1 and +1".format(mu))

    if isinstance(mu_r, np.ndarray):
        if np.any(mu_r < -1.0) or np.any(mu_r > 1.0):
            raise ValueError("rotate, mu_r array is not between -1 and +1")
    else:
        if mu_r < -1.0 or mu_r > 1.0:
            raise ValueError(
                "rotate: mu_r ({}) is not between -1 and +1".format(mu_r))

    if np.abs(azm) > (2 * np.pi):
        raise ValueError(
            "rotate: azimuth ({} deg) is not between -360 and 360".format(
                180 * (azm * 360) / np.pi))

    if isinstance(lam_r, np.ndarray):
        if np.any(np.abs(lam_r) > (2 * np.pi)):
            raise ValueError("rotate, lam_r array is not between -360 and 360")
    else:
        if np.abs(lam_r) > (2 * np.pi):
            raise ValueError(
                "rotate: lam_r ({} deg) is not between -360 and 360".format(
                    180 * lam_r / np.pi))

    # difference between azimuth and rotation angle of x-axis
    omega = lam_r - azm

    # sine of angle theta (cosine is an argument)
    # sine of angle theta-sub-r (cosine is an argument)
    sinTheta = np.sqrt((1. - mu) * (1. + mu))
    sinThr = np.sqrt((1. - mu_r) * (1. + mu_r))

    # cosine of difference between azimuth and aziumth of rotation
    cosOmega = np.cos(omega)

    # Output:
    # azimuth and cosine of angle in rotated axis system.
    # (bug if trig routines trigger error)
    aPrime = -np.arctan2(sinTheta * np.sin(omega),
                         mu_r * sinTheta * cosOmega - mu * sinThr)
    muPrime = sinTheta * sinThr * cosOmega + mu * mu_r

    return muPrime, aPrime


def yearday(year, month, day):
    """
    yearday returns the yearday for the given date.  yearday is
    the 'day of the year', sometimes called (incorrectly) 'julian day'.

    Args:
        year
        month
        day

    Returns:
        yday: day of year

    """

    assert(year >= 0)
    assert(1 <= month and month <= 12)
    assert(1 <= day and day <= numdays(year, month))

    yday = day

    # Add in number of days for preceeding months.
    for mon in range(month-1, 0, -1):
        yday += numdays(year, mon)

    return yday


def numdays(year, month):
    """
    numdays returns the number of days in the given month of
    the given year.

    Args:
        year
        month

    Returns:
        ndays: number of days in month
    """

    NDAYS = list([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    assert(year >= 0)
    assert(1 <= month and month <= 12)

    ndays = NDAYS[month-1]

    # Check for leap year for February
    if ((month == 2) and leapyear(year)):
        ndays += 1

    return ndays


def leapyear(year):
    """
    leapyear determines if the given year is a leap year or not.
    year must be positive, and must not be abbreviated; i.e.
    89 is 89 A.D. not 1989.

    Args:
        year

    Returns:
        True if a leap year, False if not a leap year
    """

    assert(year >= 0)

    if ((year % 4 == 0 and year % 100 != 0) or year % 400 == 0):
        return True
    else:
        return False
