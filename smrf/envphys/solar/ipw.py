import os
import subprocess as sp

import numpy as np

on_rtd = os.environ.get('READTHEDOCS') == 'True'
if on_rtd:
    IPW = '.'  # placehold while building the docs
elif 'IPW' not in os.environ:
    IPW = '/usr/local/bin'
else:
    IPW = os.environ['IPW']     # IPW executables


def deg_to_dms(deg):
    """
    Decimal degree to degree, minutes, seconds
    """
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]


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
