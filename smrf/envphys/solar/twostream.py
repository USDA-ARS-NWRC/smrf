import numpy as np


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
        dictionary with the following keys
        R[0] - reflectance
        R[1] - transmittance
        R[2] - direct transmittance
        R[3] - upwelling irradiance
        R[4] - total irradiance at bottom
        R[5] - direct irradiance normal to beam
    """

    if cosz <= 0:
        return {
            'reflectance': 0,
            'transmittance': 0,
            'direct_transmittance': 0,
            'upwelling_irradiance': 0,
            'irradiance_at_bottom': 0,
            'irradiance_normal_to_beam': 0
        }

    if S0 <= 0:
        raise ValueError('The direct beam irradiance (S0) is less than 0')

    if isinstance(tau, float):
        tau = np.array([tau])

    idx = tau == 0
    tau[idx] = 1e15

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

    # semi-infinite?
    idx = np.argwhere(((em == 0) & (et == 0)) | (ep >= 1e15))
    refl[idx] = omega * (gam3 * xi + alph2) / (gpx * opx)
    btrans[idx] = 0
    trans[idx] = 0

    assert(np.min(refl) >= 0)
    assert(np.min(trans) >= 0)
    assert(np.min(btrans) >= 0)
    assert(np.all(trans >= btrans * cosz))

    return {
        'reflectance': refl,
        'transmittance': trans,
        'direct_transmittance': btrans,
        'upwelling_irradiance': refl * cosz * S0,
        'irradiance_at_bottom': trans * cosz * S0,
        'irradiance_normal_to_beam': btrans * S0
    }


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
