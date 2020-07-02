import numpy as np

from smrf.envphys.constants import EMISS_TERRAIN, FREEZE, STEF_BOLTZ


def thermal_correct_terrain(th, ta, viewf):
    """
    Correct the thermal radiation for terrain assuming that
    the terrain is at the air temperature and the pixel and
    a sky view

    Args:
        th: thermal radiation
        ta: air temperature [C]
        viewf: sky view factor from view_f

    Returns:
        corrected thermal radiation

    20150611 Scott Havens
    """

    # thermal emitted from the terrain
    terrain = STEF_BOLTZ * EMISS_TERRAIN * np.power(ta + 273.15, 4)

    # correct the incoming thermal
    return viewf * th + (1 - viewf) * terrain


def precipitable_water(ta, ea):
    """
    Estimate the precipitable water from Prata (1996) :cite:`Prata:1996`
    """
    return 4650*ea/ta


def calc_long_wave(e, ta):
    """
    Apply the Stephan-Boltzman equation for longwave
    """
    return e * STEF_BOLTZ * np.power(ta, 4)


def Dilly1998(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Dilley & O'Brian
    (1998) :cite:`Dilley&OBrian:1998` using the equation:

    .. math::
        L_{clear} = 59.38 + 113.7 * \\left( \\frac{T_a}{273.16}
        \\right)^6 + 96.96 \\sqrt{w/25}

    Where :math:`T_a` is the air temperature and :math:`w` is the amount of
    precipitable water. The preipitable water is estimated as
    :math:`4650 e_o/T_o` from Prata (1996) :cite:`Prata:1996`.

    Args:
        ta: distributed air temperature [degree C]
        ea: distrubted vapor pressure [kPa]

    Returns:
        clear sky long wave radiation [W/m2]

    20170509 Scott Havens
    """

    ta = ta + FREEZE                    # convert to K
    w = precipitable_water(ta, ea)  # precipitable water

    th = 59.38 + 113.7 * (ta/273.16)**6 + 96.96*np.sqrt(w/25)

    return th


def Prata1996(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Prata (1996)
    :cite:`Prata:1996` using the equation:

    .. math::
        \\epsilon_{clear} = 1 - (1 + w) * exp(-1.2 + 3w)^{1/2}

    Where :math:`w` is the amount of precipitable water. The preipitable
    water is estimated as :math:`4650 e_o/T_o` from Prata (1996)
    :cite:`Prata:1996`.

    Args:
        ta: distributed air temperature [degree C]
        ea: distrubted vapor pressure [kPa]

    Returns:
        clear sky long wave radiation [W/m2]

    20170509 Scott Havens
    """

    ta = ta + FREEZE                    # convert to K
    w = precipitable_water(ta, ea)  # precipitable water

    # clear sky emmissivity
    ec = 1 - (1 + w) * np.exp(-np.sqrt(1.2 + 3*w))

    return calc_long_wave(ec, ta)


def Angstrom1918(ta, ea):
    """
    Estimate clear-sky downwelling long wave radiation from Angstrom (1918)
    :cite:`Angstrom:1918` as cited by Niemela et al (2001)
    :cite:`Niemela&al:2001` using the equation:

    .. math::
        \\epsilon_{clear} = 0.83 - 0.18 * 10^{-0.067 e_a}

    Where :math:`e_a` is the vapor pressure.

    Args:
        ta: distributed air temperature [degree C]
        ea: distrubted vapor pressure [kPa]

    Returns:
        clear sky long wave radiation [W/m2]

    20170509 Scott Havens
    """

    ta = ta + FREEZE                  # convert to K
    e = 0.83 - 0.18 * np.power(10, -0.067*ea)

    return calc_long_wave(e, ta)
