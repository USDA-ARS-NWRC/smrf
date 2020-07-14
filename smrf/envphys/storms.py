import numpy as np
import pandas as pd


def time_since_storm(precipitation, perc_snow, time_step=1/24, mass=1.0,
                     time=4, stormDays=None, stormPrecip=None, ps_thresh=0.5):
    """
    Calculate the decimal days since the last storm given a precip time series,
    percent snow, mass threshold, and time threshold

     - Will look for pixels where perc_snow > 50% as storm locations
     - A new storm will start if the mass at the pixel has exceeded the mass
         limit, this ensures that the enough has accumulated

    Args:
        precipitation: Precipitation values
        perc_snow: Percent of precipitation that was snow
        time_step: Step in days of the model run
        mass: Threshold for the mass to start a new storm
        time: Threshold for the time to start a new storm
        stormDays: If specified, this is the output from a previous run of
            storms else it will be set to the date_time value
        stormPrecip: Keeps track of the total storm precip

    Returns:
        tuple:
        - **stormDays** - Array representing the days since the last storm at
            a pixel
        - **stormPrecip** - Array representing the precip accumulated during
            the most recent storm

    Created Janurary 5, 2016
    @author: Scott Havens
    """
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
    stormPrecip[idx] = + precipitation[idx]

    # see if the mass threshold has been passed
    idx_mass = stormPrecip >= mass

    # reset the stormDays to zero where the storm is present
    stormDays[idx_mass] = 0

    return stormDays, stormPrecip


def time_since_storm_pixel(precipitation, dpt, perc_snow, storming,
                           time_step=1/24, stormDays=None, mass=1.0,
                           ps_thresh=0.5):
    """
    Calculate the decimal days since the last storm given a precip time series

     - Will assign decimal days since last storm to every pixel

    Args:
        precipitation: Precipitation values
        dpt: dew point values
        perc_snow: percent_snow values
        storming: if it is stomring
        time_step: step in days of the model run
        stormDays: unifrom days since last storm on pixel basis
        mass: Threshold for the mass to start a new storm
        ps_thresh: Threshold for percent_snow

    Returns:
        stormDays: days since last storm on pixel basis

    Created October 16, 2017
    @author: Micah Sandusky
    """
    # either preallocate or use the input
    if stormDays is None:
        stormDays = np.zeros(precipitation.shape)

    # add timestep
    stormDays += time_step

    # only reset if stomring and not overly warm
    if storming and dpt.min() < 2.0:
        # determine location where there is enough mass
        idx_mass = precipitation >= mass
        # determine locations where it has snowed
        idx = perc_snow >= ps_thresh

        # reset the stormDays to zero where the storm is present
        stormDays[(idx_mass & idx)] = 0

    return stormDays


def tracking_by_station(precip, mass_thresh=0.01, steps_thresh=3):
    """
    Processes the vector station data prior to the data being distributed

    Args:
        precipitation: precipitation values
        time: Time step that smrf is on
        time_steps_since_precip: time steps since the last precipitation
        storm_lst: list that store the storm cycles in order. A storm is
                    recorded by its start and its end. The list
                    is passed by reference and modified internally.
                    Each storm entry should be in the format of:
                    [{start:Storm Start, end:Storm End}]

                    e.g.
                    [
                    {start:date_time1,end:date_time2,'BOG1':100, 'ATL1':85},
                    {start:date_time3,end:date_time4,'BOG1':50, 'ATL1':45},
                    ]

                    would be a two storms at stations BOG1 and ATL1

        mass_thresh: mass amount that constitutes a real precip event,
            default = 0.01.

        steps_thresh: Number of time steps that constitutes the end of a precip
            event, default = 2 steps (typically 2 hours)

    Returns:
        tuple:
            - **storms** - A list of dictionaries containing storm start,stop,
                mass accumulated, of given storm.

            - **storm_count** - A total number of storms found

    Created April 24, 2017
    @author: Micah Johnson
    """

    storm_columns = ['start', 'end']
    stations = list(precip)
    storm_columns += stations

    storms = []

    stations = list(precip)
    is_storming = False
    time_steps_since_precip = 0

    for i, row in precip.iterrows():
        time = pd.Timestamp(i)

        # Storm Idenificiation
        if row.max() > mass_thresh:
            # Start a new storm
            if not is_storming:
                new_storm = {}
                new_storm['start'] = time
                for sta, p in row.iteritems():
                    new_storm[sta] = 0
                # Create a new row
                is_storming = True

            time_steps_since_precip = 0
            # Always add the latest end date to avoid unclosed storms
            new_storm['end'] = time

            # Accumulate precip for storm total
            for sta, mass in row.iteritems():
                new_storm[sta] += mass

        elif is_storming and time_steps_since_precip < steps_thresh:
            new_storm['end'] = time

            time_steps_since_precip += 1

        if time_steps_since_precip >= steps_thresh and is_storming:
            is_storming = False
            storms.append(new_storm)
            # print "=="*10 + "> not storming!"

    # Append the last storm if we ended during a storm
    if is_storming:
        storms.append(new_storm)

    storm_count = len(storms)

    # Make sure we have storms
    if storm_count == 0:
        empty_data = {}
        for col in storm_columns:
            empty_data[col] = []
        storms = pd.DataFrame(empty_data)
    else:
        storms = pd.DataFrame(storms)

    return storms, storm_count


def tracking_by_basin(precipitation, time, storm_lst, time_steps_since_precip,
                      is_storming, mass_thresh=0.01, steps_thresh=2):
    """
    Args:
        precipitation: precipitation values
        time: Time step that smrf is on
        time_steps_since_precip: time steps since the last precipitation
        storm_lst: list that store the storm cycles in order. A storm is
                    recorded by its start and its end. The list
                    is passed by reference and modified internally.
                    Each storm entry should be in the format of:
                    [{start:Storm Start, end:Storm End}]

                    e.g.
                         [
                         {start:date_time1,end:date_time2},
                         {start:date_time3,end:date_time4},
                         ]

                         #would be a two storms

        mass_thresh: mass amount that constitutes a real precip
                    event, default = 0.0.
        steps_thresh: Number of time steps that constitutes the end of
                        a precip event, default = 2 steps (default 2 hours)

    Returns:
        tuple:
            storm_lst - updated storm_lst
            time_steps_since_precip - updated time_steps_since_precip
            is_storming - True or False whether the storm is ongoing or not

    Created March 3, 2017
    @author: Micah Johnson
    """
    # print  "--"*10 +"> Max precip = {0}".format(precipitation.max())
    if precipitation.max() > mass_thresh:
        # Start a new storm
        if len(storm_lst) == 0 or not is_storming:
            storm_lst.append({'start': time, 'end': None})
            is_storming = True

        # always append the most recent timestep to avoid unended storms
        storm_lst[-1]['end'] = time
        time_steps_since_precip = 0

    elif is_storming and time_steps_since_precip < steps_thresh:
        time_steps_since_precip += 1

    if time_steps_since_precip >= steps_thresh:
        is_storming = False
        # print "--"*10 + "> not storming!"

    return storm_lst, time_steps_since_precip, is_storming


def clip_and_correct(precip, storms, stations=[]):
    """
    Meant to go along with the storm tracking, we correct the data here by
    adding in the precip we would miss by ignoring it. This is mostly because
    will get rain on snow events when there is snow because of the storm
    definitions and still try to distribute precip data.

    Args:
        precip: Vector station data representing the measured precipitation
        storms: Storm list with dictionaries as defined in
                :func:`~smrf.envphys.storms.tracking_by_station`
        stations: Desired stations that are being used for clipping. If
                  stations is not passed, then use all in the dataframe


    Returns:
        The correct precip that ensures there is no precip outside of the
        defined storms with the clipped amount of precip proportionally added
        back to storms.

    Created May 3, 2017
    @author: Micah Johnson
    """

    # Specify zeros where were not storming
    precip_clipped = precip.copy()
    precip_clipped[:] = 0

    for j, storm in storms.iterrows():

        storm_start = storm['start']
        storm_end = storm['end']
        my_slice = precip.loc[storm_start:storm_end]
        precip_clipped.loc[storm_start:storm_end] = my_slice

    correction = {}

    if len(stations) == 0:
        stations = precip.columns

    # Correct the precip to be equal to the sum.
    for station in stations:
        original = precip[station].sum()
        clipped = precip_clipped[station].sum()

        if original == 0:
            c = 1.0
        elif clipped == 0:
            c = 0
        else:
            c = original/clipped

        correction[station] = c

    return precip_clipped.mul(pd.Series(correction), axis=1)
