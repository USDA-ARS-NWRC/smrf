'''
Created on March 14, 2017
Originally written by Scott Havens in 2015
@author: Micah Johnson
'''

__version__ = '0.1.1'


import numpy as np
import os
from datetime import datetime

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
    stormDays - if specified, this is the output from a previous run of storms
    stormPrecip - keeps track of the total storm precip

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
#         stormDays = np.add(stormDays, 1)
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


def time_since_storm(precipitation, perc_snow, time_step=1/24, mass=1, time=4,
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
        stormDays - if specified, this is the output from a previous run of storms
            else it will be set to the date_time value
        stormPrecip - keeps track of the total storm precip

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
#         stormDays = np.add(stormDays, 1)
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


def tracking(precipitation, time, storm_lst, time_steps_since_precip, is_storming, mass_thresh = 0.01, steps_thresh=2):
    '''
    Args:
        precipitation - precipitation values
        time - Time step that smrf is on
        time_steps_since_precip - time steps since the last precipitation
        storm_lst - list that store the storm cycles in order. A storm is recorded by
                    its start and its end. The list
                    is passed by reference and modified internally.
                    Each storm entry should be in the format of:
                    [{start:Storm Start, end:Storm End}]

                    e.g.
                         [
                         {start:date_time1,end:date_time2},
                         {start:date_time3,end:date_time4},
                         ]

                         #would be a two storms

        mass_thresh - mass amount that constitutes a real precip event, default = 0.0.
        steps_thresh - Number of time steps that constitutes the end of a precip event, default = 2 steps (typically 2 hours)

    Returns:
        True or False whether the storm is ongoing or not

    Created March 3, 2017
    @author: Micah Johnson
    '''
    if precipitation.mean() > mass_thresh:
        #New storm
        if len(storm_lst)== 0 or not is_storming :
            storm_lst.append({'start':time,'end':None})
            is_storming = True

        #always append the most recent timestep to avoid unended storms
        storm_lst[-1]['end'] = time
        time_steps_since_precip = 0

    elif is_storming and time_steps_since_precip < steps_thresh:
        storm_lst[-1]['end'] = time
        time_steps_since_precip+=1


    else:
        is_storming = False

    return is_storming
