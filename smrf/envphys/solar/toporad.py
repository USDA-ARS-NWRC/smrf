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


def toporad(beam, diffuse, illum_angle, sky_view_factor, terrain_config_factor,
            cosz, surface_albedo=0.0):
    """Topographically-corrected solar radiation. Calculates the topographic
    distribution of solar radiation at a single time, using input beam and diffuse
    radiation calculates supplied by elevrad.
    """

    # adjust diffuse radiation accounting for sky view factor
    drad = diffuse * sky_view_factor

    # add reflection from adjacent terrain
    drad = drad + (diffuse * (1 - sky_view_factor) +
                   beam * cosz) * terrain_config_factor * surface_albedo

    # global radiation is diffuse + incoming_beam * cosine of local
    # illumination * angle
    rad = drad + beam * illum_angle

    return rad, drad


class Elevrad():
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

    def __init__(self, elevation, solar_irradiance, cosz, **kwargs):
        """Initialize then run elevrad

        Args:
            elevation (np.array): DEM elevation in meters
            solar_irradiance (float): from direct_solar_irradiance
            cosz (float): cosine of zenith angle
            kwargs: tau_elevation, tau, omega, scattering_factor, surface_albedo

        Returns:
            radiation: dict with beam and diffuse radiation
        """

        # defaults
        self.tau_elevation = 100.0
        self.tau = 0.2,
        self.omega = 0.85
        self.scattering_factor = 0.3
        self.surface_albedo = 0.5

        # set user specified values
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.elevation = elevation
        self.solar_irradiance = solar_irradiance
        self.cosz = cosz

        self.calculate()

    def calculate(self):
        """Perform the calculations
        """

        # reference pressure (at reference elevation, in km)
        reference_pressure = hysat(SEA_LEVEL, STD_AIRTMP, STD_LAPSE,
                                   self.tau_elevation / 1000, GRAVITY, MOL_AIR)

        # Convert each elevation in look-up table to pressure, then to optical
        # depth over the modeling domain
        pressure = hysat(SEA_LEVEL, STD_AIRTMP, STD_LAPSE,
                         self.elevation / 1000, GRAVITY, MOL_AIR)
        tau_domain = self.tau * pressure / reference_pressure

        # twostream over the optical depth of the domain
        self.twostream = twostream(
            self.cosz,
            self.solar_irradiance,
            tau=tau_domain,
            omega=self.omega,
            g=self.scattering_factor,
            R0=self.surface_albedo)

        # calculate beam and diffuse
        self.beam = self.solar_irradiance * \
            self.twostream['direct_transmittance']
        self.diffuse = self.solar_irradiance * self.cosz * \
            (self.twostream['transmittance'] -
             self.twostream['direct_transmittance'])
