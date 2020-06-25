'''
Created on Apr 15, 2015

@author: scott
'''

import numpy as np

from smrf.utils import utils


def catchment_ratios(ws, gauge_type, snowing):
    """
    Point models for catchment ratios of the
    """

    if gauge_type == "us_nws_8_shielded":
        if snowing:
            CR = np.exp(4.61 - 0.04*ws**1.75)
        else:
            CR = 101.04 - 5.62*ws

    elif gauge_type == "us_nws_8_unshielded":
        if snowing:
            CR = np.exp(4.61 - 0.16*ws**1.28)
        else:
            CR = 100.77 - 8.34*ws
    else:
        raise ValueError(
            "Unknown catchement adjustment model ----> {0}".format(gauge_type))

    #    elif type == "Hellmann unshielded":
    #        if snowing:
    #             CR = CR = 100.00 + 1.13*Ws - 19.45*Ws
    #        else:
    #             CR = 96.63 + 0.41*Ws - 9.84*Ws + 5.95 * Tmean

    # elif type == "nipher":
    #     if snowing:
    #          CR= 100.00 - 0.44*Ws - 1.98*Ws
    #     else:
    #          CR = 97.29 - 3.18*Ws+ 0.58* Tmax - 0.67*Tmin
    #
    # elif type == "tretyakov":
    #     if snowing:
    #          CR = 103.11 - 8.67 * Ws + 0.30 * Tmax
    #     else:
    #          CR =  96.99 - 4.46 *Ws + 0.88 * Tmax + 0.22*Tmin
    # Avoid corrupting data
    if np.isnan(CR):
        CR = 100.0
    # CR is in percent.
    CR = CR/100.0
    return CR


def adjust_for_undercatch(p_vec, wind, temp, sta_type, metadata):
    """
    Adjusts the vector precip station data for undercatchment. Relationships
    should be added to :func:`~smrf.envphys.precip.catchment_ratio`.

    Args:
        p_vec - The station vector data in pandas series
        wind -  The vector wind data
        temp - The vector air_temp data
        sta_type - A dictionary of station names and the type of correction
            to apply
        station_metadata - station metadata TODO merge in the station_dict
            info to metadata

    Returns:
        adj_precip - Adjust precip accoding to the corrections applied.
    """
    adj_precip = p_vec.copy()
    for sta in p_vec.index:
        if sta in temp.keys():
            T = temp[sta]
            if sta in wind.keys():
                ws = wind[sta]
                if ws > 6.0:
                    ws = 6.0

                if T < -0.5:
                    snowing = True
                else:
                    snowing = False

                if sta in sta_type.keys():
                    gauge_type = sta_type[sta]
                else:
                    gauge_type = sta_type['station_undercatch_model_default']

                cr = catchment_ratios(ws, gauge_type, snowing)
                adj_precip[sta] = p_vec[sta]/cr

    return adj_precip


def dist_precip_wind(precip, precip_temp, az, dir_round_cell, wind_speed,
                     cell_maxus, tbreak, tbreak_direction, veg_type, veg_fact,
                     cfg, mask=None):
    """
    Redistribute the precip based on wind speed and direciton
    to account for drifting.

    Args:
        precip:             distributed precip
        precip_temp:        precip_temp array
        az:                 wind direction
        dir_round_cell:     from wind module
        wind_speed:         wind speed array
        cell_maxus:         max upwind slope from maxus file
        tbreak:             relative local slope from tbreak file
        tbreak_direction:   direction array from tbreak file
        veg_type:           user input veg types to correct
        veg_factor:         interception correction for veg types. ppt mult is
                            multiplied by 1/veg_factor

    Returns:
        precip_drift:       numpy array of precip redistributed for wind

    """
    # thresholds
    tbreak_threshold = cfg['tbreak_threshold']
    min_scour = cfg['winstral_min_scour']
    max_scour = cfg['winstral_max_scour']
    min_drift = cfg['winstral_min_drift']
    max_drift = cfg['winstral_max_drift']
    precip_temp_threshold = 0.5

    # polynomial factors
    drift_poly = {}
    drift_poly['a'] = 0.0289
    drift_poly['b'] = -0.0956
    drift_poly['c'] = 1.000761
    ppt_poly = {}
    ppt_poly['a'] = 0.0001737
    ppt_poly['b'] = 0.002549
    ppt_poly['c'] = 0.03265
    ppt_poly['d'] = 0.5929

    # initialize arrays
    celltbreak = np.ones(dir_round_cell.shape)
    drift_factor = np.ones(dir_round_cell.shape)
    precip_drift = np.zeros(dir_round_cell.shape)
    pptmult = np.ones(dir_round_cell.shape)

    # classify tbreak
    dir_unique = np.unique(dir_round_cell)

    for d in dir_unique:
        # find all values for matching direction
        ind = dir_round_cell == d
        i = np.argwhere(tbreak_direction == d)[0][0]
        celltbreak[ind] = tbreak[i][ind]

    # ################################################### #
    # Routine for drift cells
    # ################################################### #
    # for tbreak cells >  threshold
    idx = ((celltbreak > tbreak_threshold) & (
        precip_temp < precip_temp_threshold))

    # calculate drift factor
    drift_factor[idx] = drift_poly['c'] * np.exp(
        drift_poly['b'] * wind_speed[idx] +
        drift_poly['a'] * wind_speed[idx]**2
    )

    # cap drift factor
    drift_factor[idx] = utils.set_min_max(
        drift_factor[idx], min_drift, max_drift)

    # multiply precip by drift factor for drift cells
    precip_drift[idx] = drift_factor[idx]*precip[idx]

    # ################################################### #
    # Now lets deal with non drift cells
    # ################################################### #

    # for tbreak cells <= threshold (i.e. the rest of them)
    idx = ((celltbreak <= tbreak_threshold) & (
        precip_temp < precip_temp_threshold))

    # reset pptmult for exposed pixels
    pptmult = np.ones(dir_round_cell.shape)

    # original from manuscript
    pptmult[idx] = ppt_poly['a'] + ppt_poly['c'] * cell_maxus[idx] - \
        ppt_poly['b'] * cell_maxus[idx]**2 + ppt_poly['a'] * cell_maxus[idx]**3

    # veg effects at indices that we are working on where veg type matches
    for i, v in enumerate(veg_fact):
        idv = ((veg_type == int(v)) & (idx))
        pptmult[idv] = pptmult[idv] * 1.0 / veg_fact[v]

    # hardcode for pine
    pptmult[(idx) & ((veg_type == 3055) | (veg_type == 3053)
                     | (veg_type == 42))] = 1.0  # 0.92
    # cap ppt mult
    pptmult[idx] = utils.set_min_max(pptmult[idx], min_scour, max_scour)

    # multiply precip by scour factor
    precip_drift[idx] = pptmult[idx] * precip[idx]

    # ############################## #
    # no precip redistribution where dew point >= threshold
    idx = precip_temp >= precip_temp_threshold
    precip_drift[idx] = precip[idx]

    return precip_drift
