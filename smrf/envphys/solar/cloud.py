import pandas as pd

from smrf.envphys.solar.model import model_solar


def cf_cloud(beam, diffuse, cf):
    """
    Correct beam and diffuse irradiance for cloud attenuation at a single
    time, using input clear-sky global and diffuse radiation calculations
    supplied by locally modified toporad or locally modified stoporad

    Args:
        beam: global irradiance
        diffuse: diffuse irradiance
        cf: cloud attenuation factor - actual irradiance / clear-sky irradiance

    Returns:
        c_grad: cloud corrected gobal irradiance
        c_drad: cloud corrected diffuse irradiance

    20150610 Scott Havens - adapted from cloudcalc.c
    """

    # define some constants
    CRAT1 = 0.15
    CRAT2 = 0.99
    CCOEF = 1.38

    # cloud attenuation, beam ratio is reduced
    bf_c = CCOEF * (cf - CRAT1)**2
    c_grad = beam * cf
    c_brad = c_grad * bf_c
    c_drad = c_grad - c_brad

    # extensive cloud attenuation, no beam
    ind = cf <= CRAT1
    c_brad[ind] = 0
    c_drad[ind] = c_grad[ind]

    # minimal cloud attenution, no beam ratio reduction
    ind = cf > CRAT2
    c_drad[ind] = diffuse[ind] * cf[ind]
    c_brad[ind] = c_grad[ind] - c_drad[ind]

    return c_grad, c_drad


def get_hrrr_cloud(df_solar, df_meta, lat, lon):
    """
    Take the combined solar from HRRR and use the two stream calculation
    at the specific HRRR pixels to find the cloud_factor.

    Args:
        df_solar - solar dataframe from hrrr
        df_meta - meta_data from hrrr
        lat - basin lat
        lon - basin lon

    Returns:
        df_cf - cloud factor dataframe in same format as df_solar input
    """

    # get and loop through the columns
    dates = df_solar.index.values[:]

    # find each cell solar at top of atmosphere for each date
    basin_sol = df_solar.copy()
    for idt, dt in enumerate(dates):
        # get solar using twostream
        dtt = pd.to_datetime(dt)
        basin_sol.iloc[idt, :] = model_solar(dtt, lat, lon)

    # if it's close to sun down or sun up, then the cloud factor gets
    # difficult to calculate
    basin_sol[basin_sol < 50] = 0
    df_solar[basin_sol < 50] = 0

    # This will produce NaN values when the sun is down
    df_cf = df_solar / basin_sol

    # linear interpolate the NaN values at night
    df_cf = df_cf.interpolate(method='linear').ffill()

    # Clean up the dataframe to be between 0 and 1
    df_cf[df_cf > 1.0] = 1.0
    df_cf[df_cf < 0.0] = 0.0

    return df_cf
