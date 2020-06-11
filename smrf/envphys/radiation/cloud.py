import pandas as pd

from smrf.envphys.radiation.model import model_solar


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


def get_hrrr_cloud(df_solar, df_meta, logger, lat, lon):
    """
    Take the combined solar from HRRR and use the two stream calculation
    at the specific HRRR pixels to find the cloud_factor.

    Args:
        df_solar - solar dataframe from hrrr
        df_meta - meta_data from hrrr
        logger - smrf logger
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

    # This would be the proper way to do this but it's too
    # computationally expensive
    # cs_solar = df_solar.copy()
    # for dt, row in cs_solar.iterrows():
    #     dtt = pd.to_datetime(dt)
    #     for ix,value in row.iteritems():
    #         # get solar using twostream only if the sun is
    # up
    #         if value > 0:
    #             cs_solar.loc[dt, ix] = model_solar(dtt,
    # df_meta.loc[ix, 'latitude'], df_meta.loc[ix, 'longitude'])

    # This will produce NaN values when the sun is down
    df_cf = df_solar / basin_sol

    # linear interpolate the NaN values at night
    df_cf = df_cf.interpolate(method='linear').ffill()

    # Clean up the dataframe to be between 0 and 1
    df_cf[df_cf > 1.0] = 1.0
    df_cf[df_cf < 0.0] = 0.0

    # # create cloud factor dataframe
    # df_cf = df_solar.copy()
    # #df_basin_sol = pd.DataFrame(index = dates, data = basin_sol)

    # # calculate cloud factor from basin solar
    # for cl in clms:
    #     cf_tmp = df_cf[cl].values[:]/basin_sol
    #     cf_tmp[np.isnan(cf_tmp)] = 0.0
    #     cf_tmp[cf_tmp > 1.0] = 1.0
    #     df_cf[cl] = cf_tmp

    # df_cf = df_solar.divide(df_basin_sol)
    # # clip to 1.0
    # df_cf = df_cf.clip(upper=1.0)
    # # fill nighttime with 0
    # df_cf = df_cf.fillna(value=0.0)

    # for idc, cl in enumerate(clms):
    #     # get lat and lon for each hrrr pixel
    #     lat = df_meta.loc[ cl,'latitude']
    #     lon = df_meta.loc[ cl,'longitude']
    #
    #     # get solar values and make empty cf vector
    #     sol_vals = df_solar[cl].values[:]
    #     cf_vals = np.zeros_like(sol_vals)
    #     cf_vals[:] = np.nan
    #
    #     # loop through time series for the pixel
    #     for idt, sol in enumerate(sol_vals):
    #         dt = pd.to_datetime(dates[idt])
    #         # get the modeled solar
    #         calc_sol = model_solar(dt, lat, lon)
    #         if calc_sol == 0.0:
    #             cf_tmp = 0.0
    #             # diff = sol - calc_sol
    #             # if diff > 5:
    #             #     print(sol)
    #         else:
    #             cf_tmp = sol / calc_sol
    #         if cf_tmp > 1.0:
    #             logger.warning('CF to large: ')
    #             logger.warning('{} for {} at {}'.format(cf_tmp, cl, idt))
    #             cf_tmp = 1.0
    #         # store value
    #         cf_vals[idt] =cf_tmp
    #
    #     # store pixel cloud factor
    #     df_cf[cl] = cf_vals

    return df_cf
