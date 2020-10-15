import numpy as np


# Coefficients for snow relationship
class Coefficients:
    TR0 = 0.5
    PCR0 = 0.25
    PC0 = 0.75


def calc_percent_snow(tpp, t_max=0.0):
    """
    Calculates the percent snow for the nasde_models piecewise_susong1999
    and marks2017.

    Args:
        tpp: A numpy array of temperature, use dew point temperature if
            available [degree C].
        t_max: Max temperature that the percent snow is estimated.
              Default is 0.0 Degrees C.

    Returns:
        numpy.array:
        A fraction of the precipitation at each pixel that is snow provided
        by tpp.
    """

    percent = np.zeros(tpp.shape)

    percent[tpp <= -0.5] = 1.0

    ind = (tpp > -0.5) & (tpp <= 0.0)
    if np.any(ind):
        percent[ind] = (-tpp[ind] / Coefficients.TR0) * \
                       Coefficients.PCR0 + Coefficients.PC0

    ind = (tpp > 0.0) & (tpp <= t_max + 1.0)
    if np.any(ind):
        percent[ind] = (-tpp[ind] / (t_max + 1.0)) * \
                       Coefficients.PC0 + Coefficients.PC0

    return percent


def check_temperature(tpp, t_max=0.0, t_min=-10.0):
    """
    Sets  the precipitation temperature and snow temperature.

    Args:
        tpp: A numpy array of temperature, use dew point temperature
            if available [degrees C].
        t_max: Thresholds the max temperature of the snow [degrees C].
        t_min: Minimum temperature that the precipitation temperature
            [degrees C].

    Returns:
        tuple:
           - **tpp** (*numpy.array*) - Modified precipitation temperature
                     that limited to a minimum set by t_min.
           - **t_snow** (*numpy.array*) - Temperature of the surface of the
                         snow set by the precipitation temperature and
                         limited by t_max, where t_snow > t_max = t_max.

    """

    tpp[tpp < t_min] = t_min

    t_snow = tpp.copy()
    t_snow[tpp > t_max] = t_max

    return tpp, t_snow
