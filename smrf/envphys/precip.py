'''
Created on Apr 15, 2015

@author: scott
'''

import numpy as np

from smrf.utils import utils


def mkprecip(precipitation, temperature):
    '''
    Follows the IPW command mkprecip

    The precipitation phase, or the amount of precipitation falling as rain or
    snow, can significantly alter the energy and mass balance of the snowpack,
    either leading to snow accumulation or inducing melt :cite:`Marks&al:1998`
    :cite:`Kormos&al:2014`. The precipitation phase and initial snow density
    are based on the precipitation temperature (the distributed dew point
    temperature) and are estimated after Susong et al (1999)
    :cite:`Susong&al:1999`. The table below shows the relationship to
    precipitation temperature:

    ========= ======== ============ ===============
    Min Temp  Max Temp Percent snow Snow density
    [deg C]   [deg C]  [%]          [kg/m^3]
    ========= ======== ============ ===============
    -Inf      -5       100          75
    -5        -3       100          100
    -3        -1.5     100          150
    -1.5      -0.5     100          175
    -0.5      0        75           200
    0         0.5      25           250
    0.5       Inf      0            0
    ========= ======== ============ ===============

    Args:
        precipitation - array of precipitation values [mm]
        temperature - array of temperature values, use dew point temperature
            if available [degree C]

    Output:
        returns the percent snow and estimated snow density
    '''

    # convert the inputs to numpy arrays
    precipitation = np.array(precipitation)
    temperature = np.array(temperature)

    # create a list from the table above
    t = []
    t.append({'temp_min': -1e309, 'temp_max': -5, 'snow': 1, 'density': 75})
    t.append({'temp_min': -5, 'temp_max': -3, 'snow': 1, 'density': 100})
    t.append({'temp_min': -3, 'temp_max': -1.5, 'snow': 1, 'density': 150})
    t.append({'temp_min': -1.5, 'temp_max': -0.5, 'snow': 1, 'density': 175})
    t.append({'temp_min': -0.5, 'temp_max': 0.0, 'snow': 0.75, 'density': 200})
    t.append({'temp_min': 0.0, 'temp_max': 0.5, 'snow': 0.25, 'density': 250})
    t.append({'temp_min': 0.5, 'temp_max': 1e309, 'snow': 0, 'density': 0})

    # preallocate the percent snow (ps) and snow density (sd)
    ps = np.zeros(precipitation.shape)
    sd = np.zeros(ps.shape)

    # if no precipitation return all zeros
    if np.sum(precipitation) == 0:
        return ps, sd

    # determine the indicies and allocate based on the table above
    for row in t:

        # get the values between the temperature ranges that have precip
        ind = [(temperature >= row['temp_min']) &
               (temperature < row['temp_max'])]

        # set the percent snow
        ps[ind] = row['snow']

        # set the density
        sd[ind] = row['density']

    # if there is no precipitation at a pixel, don't report a value
    # this may make isnobal crash, I'm not really sure
    ps[precipitation == 0] = 0
    sd[precipitation == 0] = 0

    return ps, sd


def storms(precipitation, perc_snow, mass=1, time=4,
           stormDays=None, stormPrecip=None, ps_thresh=0.5):
    '''
    Calculate the decimal days since the last storm given a precip time series,
    percent snow, mass threshold, and time threshold

     - Will look for pixels where perc_snow > 50% as storm locations
     - A new storm will start if the mass at the pixel has exceeded the mass
         limit, this ensures that the enough has accumulated

    Args:
        precipitation - precipitation values
        perc_snow - precent of precipitation that was snow
        mass - threshold for the mass to start a new storm
        time - threshold for the time to start a new storm
        stormDays - if specified, this is the output from a previous run
            of storms
        stormPrecip - keeps track of the total storm precip

    Returns:
        (stormDays, stormPrecip) - the timesteps since the last storm
            and the total precipitation for the storm
    Created April 17, 2015
    @author: Scott Havens
    '''

    # either preallocate or use the input
    if stormDays is None:
        stormDays = np.zeros(precipitation.shape)

    if stormPrecip is None:
        stormPrecip = np.zeros(precipitation.shape)

    # if there is no snow, don't reset the counter
    # This ensures that the albedo won't be reset
    stormDays += 1
    if np.sum(perc_snow) == 0:
        stormPrecip = np.zeros(precipitation.shape)
        return stormDays, stormPrecip

    # determine locations where it has snowed
    idx = perc_snow >= ps_thresh

    # determine locations where the time threshold has passed
    # these areas, the stormPrecip will be set back to zero
    idx_time = stormDays >= time
    stormPrecip[idx_time] = 0

    # add the values to the stormPrecip
    stormPrecip[idx] =+ precipitation[idx]

    # see if the mass threshold has been passed
    idx_mass = stormPrecip >= mass

    # reset the stormDays to zero where the storm is present
    stormDays[idx_mass] = 0

    return stormDays, stormPrecip


def storms_time(precipitation, perc_snow, time_step=1/24, mass=1, time=4,
                stormDays=None, stormPrecip=None, ps_thresh=0.5):
    '''
    Calculate the decimal days since the last storm given a precip time series,
    percent snow, mass threshold, and time threshold

     - Will look for pixels where perc_snow > 50% as storm locations
     - A new storm will start if the mass at the pixel has exceeded the mass
         limit, this ensures that the enough has accumulated

    Args:
        precipitation - precipitation values
        perc_snow - precent of precipitation that was snow
        time_step: step in days of the model run
        mass - threshold for the mass to start a new storm
        time - threshold for the time to start a new storm
        stormDays - if specified, this is the output from a previous run
            of storms else it will be set to the date_time value
        stormPrecip - keeps track of the total storm precip

    Returns:
        (stormDays, stormPrecip) - the timesteps since the last storm
            and the total precipitation for the storm

    Created Janurary 5, 2016
    @author: Scott Havens
    '''

    # either preallocate or use the input
    if stormDays is None:
        stormDays = np.zeros(precipitation.shape)

    if stormPrecip is None:
        stormPrecip = np.zeros(precipitation.shape)

    # if there is no snow, don't reset the counter
    # This ensures that the albedo won't be reset
    stormDays += time_step
    if np.sum(perc_snow) == 0:
        stormPrecip = np.zeros(precipitation.shape)
        return stormDays, stormPrecip

    # determine locations where it has snowed
    idx = perc_snow >= ps_thresh

    # determine locations where the time threshold has passed
    # these areas, the stormPrecip will be set back to zero
    idx_time = stormDays >= time
    stormPrecip[idx_time] = 0

    # add the values to the stormPrecip
    stormPrecip[idx] =+ precipitation[idx]

    # see if the mass threshold has been passed
    idx_mass = stormPrecip >= mass

    # reset the stormDays to zero where the storm is present
    stormDays[idx_mass] = 0

    return stormDays, stormPrecip

def catchment_ratios(ws, gauge_type, snowing):
    """
    Point models for catchment ratios of the
    """

    if gauge_type == "us_nws_8_shielded":
        if snowing:
             CR =  np.exp(4.61 - 0.04*ws**1.75)
        else:
             CR = 101.04 - 5.62*ws

    elif gauge_type == "us_nws_8_unshielded":
         if snowing:
              CR = np.exp(4.61 - 0.16*ws**1.28)
         else:
              CR = 100.77 - 8.34*ws
    else:
         raise ValueError("Unknown catchement adjustment model ----> {0}".format(gauge_type))


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
    #Avoid corrupting data
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
        sta_type - A dictionary of station names and the type of correction to apply
        station_metadata - station metadata TODO merge in the station_dict info to metadata

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
                    snowing=True
                else:
                    snowing=False

                if sta in sta_type.keys():
                    gauge_type = sta_type[sta]
                else:
                    gauge_type = sta_type['station_undercatch_model_default']

                cr = catchment_ratios(ws,gauge_type,snowing)
                adj_precip[sta] = p_vec[sta]/cr
                #print(adj_precip[sta],p_vec[sta],cr)

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
    tbreak_threshold =  cfg['tbreak_threshold']
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
    idx = ((celltbreak > tbreak_threshold) & (precip_temp < precip_temp_threshold))
    # calculate drift factor
    drift_factor[idx] = drift_poly['c'] * np.exp(drift_poly['b'] * wind_speed[idx] \
                        + drift_poly['a'] * wind_speed[idx]**2);
    # cap drift factor
    drift_factor[idx] = utils.set_min_max(drift_factor[idx], min_drift, max_drift)

    # multiply precip by drift factor for drift cells
    precip_drift[idx] = drift_factor[idx]*precip[idx]

    # ################################################### #
    # Now lets deal with non drift cells
    # ################################################### #

    # for tbreak cells <= threshold (i.e. the rest of them)
    idx = ((celltbreak <= tbreak_threshold) & (precip_temp < precip_temp_threshold))
    # reset pptmult for exposed pixels
    pptmult = np.ones(dir_round_cell.shape)
    # original from manuscript
    pptmult[idx] = ppt_poly['a'] + ppt_poly['c'] * cell_maxus[idx] - ppt_poly['b'] * cell_maxus[idx]**2 \
                   + ppt_poly['a'] * cell_maxus[idx]**3;

    # veg effects at indices that we are working on where veg type matches
    for i, v in enumerate(veg_fact):
        idv = ( (veg_type == int(v)) & (idx) )
        pptmult[idv] = pptmult[idv] *  1.0 / veg_fact[v]

    # hardcode for pine
    pptmult[(idx) & ((veg_type == 3055) | (veg_type == 3053) | (veg_type == 42))] = 1.0 #0.92
    # cap ppt mult
    pptmult[idx] = utils.set_min_max(pptmult[idx], min_scour, max_scour)
    # multiply precip by scour factor
    precip_drift[idx] = pptmult[idx] * precip[idx];

    # ############################## #
    # no precip redistribution where dew point >= threshold
    idx = precip_temp >= precip_temp_threshold
    precip_drift[idx] = precip[idx]

    return precip_drift
