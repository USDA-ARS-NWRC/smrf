import numpy as np
from topocalc.horizon import horizon
from topocalc.shade import shade

from smrf.envphys.solar.twostream import mwgamma, twostream
from smrf.envphys.thermal.topotherm import hysat
from smrf.envphys.constants import SEA_LEVEL, STD_LAPSE, \
    GRAVITY, MOL_AIR, STD_AIRTMP


def stoporad():
    """stoporad simulates topographic radiation over snow-covered terrain.
    Uses a two-stream atmospheric radiation model.
    """

    pass


def toporad():
    """Topographically-corrected solar radiation.
    Calculates the topographic distribution of solar radiation at a single
    time, using input beam and diffuse radiation calculates supplied by
    elevrad.
    """
    pass


def elevrad(elevation, solar_irradiance, cosz, tau_elevation=100.0, tau=0.2,
            omega=0.85, scattering_factor=0.3, surface_albedo=0.5):
    """Beam and diffuse radiation from elevation.
    elevrad is essentially the spatial or grid v ersion of the twostream
    command.

    Args:
        elevation (np.array): DEM elevations in meters
        solar_irradiance (float): from direct_solar_irradiance
        cosz (float): cosine of zenith angle
        tau_elevation (float, optional): Elevation [m] of optical depth measurement. Defaults to 100.
        tau (float, optional): optical depth at tau_elevation. Defaults to 0.2.
        omega (float, optional): Single scattering albedo. Defaults to 0.85.
        scattering_factor (float, optional): Scattering asymmetry parameter. Defaults to 0.3.
        surface_albedo (float, optional): Mean surface albedo. Defaults to 0.5.
    """

    # reference pressure (at reference elevation, in km)
    reference_pressure = hysat(SEA_LEVEL, STD_AIRTMP, STD_LAPSE,
                               tau_elevation / 1000, GRAVITY, MOL_AIR)

    # Convert each elevation in look-up table to pressure, then to optical
    # depth over the modeling domain
    pressure = hysat(SEA_LEVEL, STD_AIRTMP, STD_LAPSE,
                     elevation / 1000, GRAVITY, MOL_AIR)
    tau_domain = tau * pressure / reference_pressure

    # twostream over the optical depth of the domain
    rad = twostream(cosz, solar_irradiance, tau=tau_domain, omega=omega,
                    g=scattering_factor, R0=surface_albedo)

    return rad
