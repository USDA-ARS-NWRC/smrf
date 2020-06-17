import numpy as np


def solar_veg_beam(data, height, cosz, k):
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


def solar_veg_diffuse(data, tau):
    """
    Apply the vegetation correction to the diffuse irradiance
    using the equation from Links and Marks 1999

    S_d,f = tau * S_d,o

    20150610 Scott Havens
    """

    return tau * data
