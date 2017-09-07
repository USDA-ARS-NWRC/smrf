"""
20160104 Scott Havens

Collection of utility functions
"""

import numpy as np
from datetime import datetime
import pytz
import os
import io
from shutil import copyfile

__version__ = '0.2.5'


def nan_helper(y):
        """Helper to handle indices and logical indices of NaNs.

        Input:
            - y, 1d numpy array with possible NaNs
        Output:
            - nans, logical indices of NaNs
            - index, a function, with signature indices=index(logical_indices)
              to convert logical indices of NaNs to 'equivalent' indices
        Example:
            >>> # linear interpolation of NaNs
            >>> nans, x= nan_helper(y)
            >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
        """

        return np.isnan(y), lambda z: z.nonzero()[0]


def set_min_max(data, min_val, max_val):
    """
    Ensure that the data is in the bounds of min and max
    20150611 Scott Havens
    """
    if max_val == None:
        max_val = np.inf
    if min_val == None:
        min_val = -np.inf

    ind = np.isnan(data)

    data[data <= min_val] = min_val
    data[data >= max_val] = max_val

    data[ind] = np.nan

    return data


def water_day(indate):
    """
    Determine the decimal day in the water year

    Args:
        indate: datetime object

    Returns:
        dd: decimal day from start of water year

    20160105 Scott Havens
    """
    tp = indate.timetuple()

    # create a test start of the water year
    test_date = datetime(tp.tm_year, 10, 1, 0, 0, 0)
    test_date = test_date.replace(tzinfo=pytz.timezone(indate.tzname()))

    # check to see if it makes sense
    if indate < test_date:
        wy = tp.tm_year
    else:
        wy = tp.tm_year + 1

    # actual water year start
    wy_start = datetime(wy-1, 10, 1, 0, 0, 0)
    wy_start = wy_start.replace(tzinfo=pytz.timezone(indate.tzname()))

    # determine the decimal difference
    d = indate - wy_start
    dd = d.days + d.seconds/86400.0

    return dd, wy


def is_leap_year(year):
    return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0

def backup_input(data, config):
    """
    Backs up input data files so a user can rerun a run with the exact data used
    for a run.
    """
    print config['topo']

    #Make the output dir
    backup_dir = os.path.join(config['output']['out_location'], 'input_backup')
    if not os.path.isdir(backup_dir):
        os.mkdir(backup_dir)
    csv_names = {}

    #Check config file for csv section and remove alternate data sets form config
    if 'csv' not in config.keys():
        config['csv'] = {}

    if 'mysql' in config.keys():
        config.pop('mysql', None)

    if 'gridded' in config.keys():
        raise ValueError("Micah_o was unsure how to handle this scenario... please advise")

    #Output station data to CSV
    for k in data.variables:
        fname = os.path.join(backup_dir,k+'.csv')
        v = getattr(data,k)
        v.to_csv(fname)

        #Adjust and output the inifile
        config['csv'][k] = fname

    #Copy topo files over to backup
    ignore = ['basin_lon','basin_lat','type']
    for s in config['topo']:
        print  config['topo'][s]
        if s not in ignore:
            src = config['topo'][s]
            dst =  os.path.join(backup_dir,os.path.split(src)[-1])
            print src,dst
            config["topo"][s] = dst
            copyfile(src, dst)

    #output inifile
    io.generate_config(config,os.path.join(backup_dir,'backup_config.ini'))
