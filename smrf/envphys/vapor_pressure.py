import numpy as np

from smrf.envphys.constants import BOIL, FREEZE, SEA_LEVEL


def satw(tk):
    """
    Saturation vapor pressure of water. from IPW satw

    Args:
        tk: temperature in Kelvin

    Returns:
        saturated vapor pressure over water

    20151027 Scott Havens
    """

    # remove bad values
    tk[tk < 0] = np.nan

    l10 = np.log(10.0)

    btk = BOIL/tk
    x = -7.90298*(btk - 1.0) + 5.02808*np.log(btk)/l10 - \
        1.3816e-7*(np.power(10.0, 1.1344e1*(1.0 - tk/BOIL))-1.) + \
        8.1328e-3*(np.power(10.0, -3.49149*(btk - 1.0)) - 1.0) + \
        np.log(SEA_LEVEL)/l10

    x = np.power(10.0, x)

    return x


def sati(tk):
    """
    saturation vapor pressure over ice. From IPW sati

    Args:
        tk: temperature in Kelvin

    Returns:
        saturated vapor pressure over ice

    20151027 Scott Havens
    """

    # remove bad values
    tk[tk < 0] = np.nan

    # preallocate
    x = np.empty(tk.shape)

    # vapor above freezing
    ind = tk > FREEZE
    x[ind] = satw(tk[ind])

    # vapor below freezing
    l10 = np.log(10.0)
    x[~ind] = 100.0 * np.power(10.0, -9.09718*((FREEZE/tk[~ind]) - 1.0) -
                               3.56654*np.log(FREEZE/tk[~ind])/l10 +
                               8.76793e-1*(1.0 - (tk[~ind]/FREEZE)) +
                               np.log(6.1071)/l10)

    return x


def idewpt(vp):
    """
    Calculate the dew point given the vapor pressure

    Args:
        vp - array of vapor pressure values in [Pa]

    Returns:
        dewpt - array same size as vp of the calculated
            dew point temperature [C] (see Dingman 2002).

    """

    # ensure that vp is a numpy array
    vp = np.array(vp)

    # take the log and convert to kPa
    vp = np.log(vp/float(1000))

    # calculate the vapor pressure
    Td = (vp + 0.4926) / (0.0708 - 0.00421*vp)

    return Td


def rh2vp(ta, rh):
    """
    Calculate the vapor pressure given the air temperature
    and relative humidity

    Args:
        ta: array of air temperature in [C]
        rh: array of relative humidity from 0-100 [%]

    Returns:
        vapor pressure
    """

    if rh.flat[0] >= 1.0:
        rh = rh/100.0

    satvp = sati(ta + 273.15)

    return satvp * rh


def satvp(dpt):
    """
    Calculate the saturation vapor pressure at the dew point
    temperature.

    Args:
        dwpt: array of dew point temperature in [C]

    Returns
       vapor_pressure
    """

    return sati(dpt + 273.15)
