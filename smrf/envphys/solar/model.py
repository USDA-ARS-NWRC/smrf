import logging

from topocalc.shade import shade

from smrf.envphys import sunang
from smrf.envphys.solar.irradiance import direct_solar_irradiance
from smrf.envphys.solar.twostream import twostream


def shade_thread(queue, date, sin_slope, aspect, zenith=None):
    """
    See shade for input argument descriptions

    Args:
        queue: queue with illum_ang, cosz, azimuth
        date_time: loop through dates to accesss
        sin_slope: numpy array of sine of slope angles sin(S)
        aspect: numpy array of aspect in radians from south
        azimuth: azimuth in degrees to the sun -180..180 (comes from sunang)
        zenith: the solar zenith angle 0..90 degrees

    """

    for v in ['cosz', 'azimuth', 'illum_ang']:
        if v not in queue.keys():
            raise ValueError('Queue must have {} key'.format(v))

    log = logging.getLogger(__name__)

    for t in date:

        log.debug('%s Calculating illumination angle' % t)

        mu = None
        cosz = queue['cosz'].get(t)

        if cosz > 0:
            azimuth = queue['azimuth'].get(t)
            mu = shade(sin_slope, aspect, azimuth, cosz, zenith)

        queue['illum_ang'].put([t, mu])


def model_solar(dt, lat, lon, tau=0.2, tzone=0):
    """
    Model solar radiation at a point
    Combines sun angle, solar and two stream

    Args:
        dt - datetime object
        lat - latitude
        lon - longitude
        tau - optical depth
        tzone - time zone

    Returns:
        corrected solar radiation
    """

    # determine the sun angle
    cosz, az, rad_vec = sunang.sunang(dt, lat, lon)

    # calculate the solar irradiance
    sol = direct_solar_irradiance(dt, [0.28, 2.8])

    # calculate the two stream model value
    R = twostream(cosz, sol, tau=tau)

    return R['irradiance_at_bottom']
