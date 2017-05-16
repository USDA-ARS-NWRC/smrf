'''
Created on March 14, 2017
Originally written by Scott Havens in 2015
@author: Micah Johnson
'''

__version__ = '0.2.1'


import numpy as np
import os
from datetime import datetime
import pandas as pd
import pytz

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

def time_since_storm_basin(precipitation, storm, stormid, storming, time, time_step=1/24, stormDays=None):
    '''
    Calculate the decimal days since the last storm given a precip time series,
    days since last storm in basin, and if it is currently storming

     - Will assign uniform decimal days since last storm to every pixel

    Args:
        precipitation - precipitation values
        storm - current or most recent storm
        time_step: step in days of the model run
        last_storm_day_basin - time since last storm for the basin
        stormid - ID of current storm
        storming - if it is currently storming
        time - current time
        stormDays - unifrom days since last storm on pixel basis

    Created May 9, 2017
    @author: Scott Havens modified by Micah Sandusky
    '''

    # either preallocate or use the input
    if stormDays is None:
        stormDays = np.zeros(precipitation.shape)
    
    #if before first storm, just add timestep
    if not storming and time <= storm['start'] and stormid == 0:
        stormDays += time_step
    # if during a storm than reset to zero
    elif time <= storm['end']:
        stormDays = np.zeros(precipitation.shape)
    # else assign uniform to days from last storm for the basin
    else:
        stormDays += time_step

    return stormDays

def tracking_by_station(precip, mass_thresh = 0.01, steps_thresh = 3):
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

    Created April 24, 2017
    @author: Micah Johnson
    '''
    storm_columns = ['start','end']
    stations = list(precip)
    storm_columns+=stations

    storms = []

    stations = list(precip)
    is_storming = False
    time_steps_since_precip= 0
    tzinfo = pytz.timezone('UTC')

    for i,row in precip.iterrows():
        time = pd.Timestamp(i)

        #Storm Idenificiation
        if row.max() > mass_thresh:
            #Start a new storm
            if not is_storming:
                new_storm = {}
                new_storm['start'] = time
                for sta,precip in row.iteritems():
                    new_storm[sta] = 0
                #Create a new row
                is_storming = True
                #print "=="*10 + "> New storm!"

            time_steps_since_precip = 0
            #Always add the latest end date to avoid unclosed storms
            new_storm['end'] = time

            #Accumulate precip for storm total
            for sta,mass in row.iteritems():
                new_storm[sta] += mass


        elif is_storming and time_steps_since_precip < steps_thresh:
            #storm_lst[-1]['end'] = time
            new_storm['end'] = time

            time_steps_since_precip+=1
            #print  "=="*10 +"> Hours since precip = {0}".format(time_steps_since_precip)
            #print "=="*10 + "> still storming but no precip!"

        if time_steps_since_precip >= steps_thresh and is_storming:
            is_storming = False
            storms.append(new_storm)
            #print "=="*10 + "> not storming!"

    #Append the last storm if we ended during a storm
    if is_storming:
        storms.append(new_storm)

    storm_count = len(storms)

    #Make sure we have storms
    if storm_count == 0:
        empty_data = {}
        for col in storm_columns:
            empty_data[col] = []
        storms = pd.DataFrame(empty_data)
    else:
        storms = pd.DataFrame(storms)

    return storms,storm_count

def tracking_by_basin(precipitation, time, storm_lst, time_steps_since_precip, is_storming, mass_thresh = 0.01, steps_thresh=2):
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
    # print  "--"*10 +"> Max precip = {0}".format(precipitation.max())
    if precipitation.max() > mass_thresh:
        #Start a new storm
        if len(storm_lst)== 0 or not is_storming :
            storm_lst.append({'start':time,'end':None})
            is_storming = True
            # print "--"*10 + "> New storm!"

        #always append the most recent timestep to avoid unended storms
        storm_lst[-1]['end'] = time
        time_steps_since_precip = 0
        #print "--"*10 + "> still storming!"


    elif is_storming and time_steps_since_precip < steps_thresh:
        #storm_lst[-1]['end'] = time
        time_steps_since_precip+=1
        # print  "--"*10 +"> Hours since precip = {0}".format(time_steps_since_precip)
        # print "--"*10 + "> still storming but no precip!"


    if time_steps_since_precip >= steps_thresh:
        is_storming = False
        # print "--"*10 + "> not storming!"


    return storm_lst, time_steps_since_precip, is_storming


def clip_and_correct(precip,storms):
    """
    Meant to go along with the storm tracking, we correct the data here by adding in
    the precip we would miss by ignoring it. This is mostly because will get rain on snow events
    when there is snow because of the storm definitions and still try to distribute precip
    data.
    Created May 3, 2017
    @author: Micah Johnson
    """

    #Specify zeros where were not storming

    precip_clipped = precip.copy()

    precip_clipped[:]=0

    for j,storm in storms.iterrows():

        storm_start = storm['start']
        storm_end = storm['end']
        my_slice= precip.ix[storm_start:storm_end]
        precip_clipped.ix[storm_start:storm_end] = my_slice

    #Determine how much precip we missed from clipping
    missed_precip = precip-precip_clipped


    correction = {}

    #Correct the precip
    #print "Amount of Precip Missed:\n"
    for station in missed_precip.columns:
        missed = missed_precip[station].sum()
        original = precip[station].sum()
        if original == 0:
            c = 0
        else:
            c = missed/original

        correction[station] = c
        precip_clipped[station]*=(1+correction[station])
        #print "{0}\t{1}".format(station,c)

    #print "Conservation of mass check (precip - precip_clipped):"
    #print precip.sum() - precip_clipped.sum()
    return precip_clipped
