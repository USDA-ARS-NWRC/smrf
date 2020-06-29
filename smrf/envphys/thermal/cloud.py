import numpy as np

from smrf.envphys.constants import FREEZE, STEF_BOLTZ
from smrf.envphys.thermal.clear_sky import calc_long_wave


def Garen2005(th, cloud_factor):
    """
    Cloud correction is based on the relationship in Garen and Marks (2005)
    :cite:`Garen&Marks:2005` between the cloud factor and measured long
    wave radiation using measurement stations in the Boise River Basin.

    .. math::
        L_{cloud} = L_{clear} * (1.485 - 0.488 * cloud\\_factor)

    Args:
        th: clear sky thermal radiation [W/m2]
        cloud_factor: fraction of sky that are not clouds, 1 equals no clouds,
            0 equals all clouds

    Returns:
        cloud corrected clear sky thermal radiation

    20170515 Scott Havens
    """

    return th * (1.485 - 0.488 * cloud_factor)


def Unsworth1975(th, ta, cloud_factor):
    """
    Cloud correction is based on Unsworth and Monteith (1975)
    :cite:`Unsworth&Monteith:1975`

    .. math::
            \\epsilon_a = (1 - 0.84) \\epsilon_{clear} + 0.84c

    where :math:`c = 1 - cloud\\_factor`

    Args:
        th: clear sky thermal radiation [W/m2]
        ta: temperature in Celcius that the clear sky thermal radiation was
            calcualted from [C] cloud_factor: fraction of sky that are not
            clouds, 1 equals no clouds, 0 equals all clouds

    Returns:
        cloud corrected clear sky thermal radiation

    20170515 Scott Havens
    """

    c = 1 - cloud_factor
    ta = ta + FREEZE

    # calculate the clear sky emissivity
    ec = th/(STEF_BOLTZ * np.power(ta, 4))

    # adjsut the atmospheric emissivity for clouds
    ea = (1 - 0.84*c) * ec + 0.84*c

    return calc_long_wave(ea, ta)


def Kimball1982(th, ta, ea, cloud_factor):
    """
    Cloud correction is based on Kimball et al. (1982) :cite:`Kimball&al:1982`

    .. math::

        L_d &= L_{clear} + \\tau_8 c f_8 \\sigma T^{4}_{c}

        \\tau_8 &= 1 - \\epsilon_{8z} (1.4 - 0.4 \\epsilon_{8z})

        \\epsilon_{8z} &= 0.24 + 2.98 \\times 10^{-6} e^2_o exp(3000/T_o)

        f_8 &= -0.6732 + 0.6240 \\times 10^{-2} T_c - 0.9140
        \\times 10^{-5} T^2_c

    where the original Kimball et al. (1982) :cite:`Kimball&al:1982` was for
    multiple cloud layers, which was simplified to one layer. :math:`T_c` is
    the cloud temperature and is assumed to be 11 K cooler than :math:`T_a`.

    Args:
        th: clear sky thermal radiation [W/m2]
        ta: temperature in Celcius that the clear sky thermal radiation was
            calcualted from [C]
        ea: distrubted vapor pressure [kPa]
        cloud_factor: fraction of sky that are not clouds, 1 equals no clouds,
            0 equals all clouds

    Returns:
        cloud corrected clear sky thermal radiation

    20170515 Scott Havens
    """

    ta = ta + FREEZE
    Tc = ta - 11

    f8 = -0.6732 + 0.6240 * 10**(-2) * Tc - 0.9140 * 10**(-5) * Tc**2
    e8z = 0.24 + 2.98 * 10**(-6) * ea**2 * np.exp(3000/ta)
    t8 = 1 - e8z * (1.4 - 0.4 * e8z)

    return th + calc_long_wave(f8 * e8z * t8, ta)


def Crawford1999(th, ta, cloud_factor):
    """
    Cloud correction is based on Crawford and Duchon (1999)
    :cite:`Crawford&Duchon:1999`

    .. math::
            \\epsilon_a = (1 - cloud\\_factor) +
            cloud\\_factor * \\epsilon_{clear}

    where :math:`cloud\\_factor` is the ratio of measured solar radiation
    to the clear sky irradiance.

    Args:
        th: clear sky thermal radiation [W/m2]
        ta: temperature in Celcius that the clear sky thermal radiation was
            calcualted from [C]
        cloud_factor: fraction of sky that are not clouds, 1 equals no clouds,
            0 equals all clouds

    Returns:
        cloud corrected clear sky thermal radiation

    20170515 Scott Havens
    """

    return calc_long_wave(1 - cloud_factor, ta + FREEZE) + cloud_factor * th
