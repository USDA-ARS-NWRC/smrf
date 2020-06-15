import numpy as np
from topocalc.horizon import horizon
from topocalc.shade import shade

from smrf.envphys.solar.twostream import mwgamma, twostream
from smrf.envphys.thermal.topotherm import hysat
from smrf.envphys.albedo import albedo
from smrf.envphys.constants import SEA_LEVEL, STD_LAPSE, \
    GRAVITY, MOL_AIR, STD_AIRTMP


def stoporad_ipw(tau_elevation, tau, omega, scattering_factor,
                 wavelength_range, start, current_day, time_zone,
                 year, latitude, longitude, cosz, azimuth,
                 grain_size, max_grain, dirt, solar_irradiance, topo):
    """stoporad simulates topographic radiation over snow-covered terrain.
    Uses a two-stream atmospheric radiation model.

    This is mainly for ensuring that the stoporad calculation is correct
    when compared with IPW. There will be ways to speed this up

    vis_cmd = 'stoporad -z %i -t %s -w %s -g %s -x 0.28,0.7 -s %s'\
            ' -d %s -f %i -y %i -A %f,%f -a %i -m %i -c %i -D %s > %s' \
            % (self.config['clear_opt_depth'],
               str(self.config['clear_tau']),
               str(self.config['clear_omega']),
               str(self.config['clear_gamma']),
               str(min_storm_day),
               str(wy_day),
               tz_min_west,
               wyear,
               cosz,
               azimuth,
               self.albedoConfig['grain_size'],
               self.albedoConfig['max_grain'],
               self.albedoConfig['dirt'],
               self.stoporad_in,
               self.vis_file)
    """

    # check cosz if sun is down
    if cosz < 0:
        return None

    else:
        # Run horizon to get sun-below-horizon mask
        horizon_angles = horizon(azimuth, topo.dem, topo.dx)
        thresh = np.tan(np.pi / 2 - np.arccos(cosz))
        no_sun_mask = np.tan(np.abs(horizon_angles)) > thresh

        # Run shade to get cosine local illumination angle
        # mask by horizon mask using cosz=0 where the sun is not visible
        illum_ang = shade(topo.sin_slope, topo.aspect, azimuth, cosz)
        illum_ang[no_sun_mask] = 0

        # Run ialbedo to get albedo
        if isinstance(start, float):
            alb_v, alb_ir = albedo(
                start * np.ones_like(topo.dem), illum_ang, grain_size,
                max_grain, dirt)
        else:
            alb_v, alb_ir = albedo(
                start, illum_ang, grain_size, max_grain, dirt)

        # Run imgstat to get R0: mean albedo
        R0_vis = np.mean(alb_v)
        R0_ir = np.mean(alb_ir)

        # Run elevrad to get beam & diffuse (if -r option not specified)
        evrad = Elevrad(
            topo.dem,
            solar_irradiance,
            cosz,
            tau_elevation=tau_elevation,
            tau=tau,
            omega=omega,
            scattering_factor=scattering_factor,
            surface_albedo=R0_vis)

        # Form input file and run toporad
        trad_beam, trad_diff = toporad(
            evrad.beam,
            evrad.diffuse,
            illum_ang,
            topo.sky_view_factor,
            topo.terrain_config_factor,
            cosz,
            surface_albedo=alb_v)

    return trad_beam, trad_diff


def toporad(beam, diffuse, illum_angle, sky_view_factor, terrain_config_factor,
            cosz, surface_albedo=0.0):
    """Topographically-corrected solar radiation. Calculates the topographic
    distribution of solar radiation at a single time, using input beam and
    diffuse radiation calculates supplied by elevrad.

    Args:
        beam (np.array): beam radiation
        diffuse (np.array): diffuse radiation
        illum_angle (np.array): local illumination angles
        sky_view_factor (np.array): sky view factor
        terrain_config_factor (np.array): terrain configuraiton factor
        cosz (float): cosine of the zenith
        surface_albedo (float/np.array, optional): surface albedo. Defaults to 0.0.

    Returns:
        tuple: beam and diffuse radiation corrected for terrain
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
