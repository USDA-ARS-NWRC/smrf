"""
20160104 Scott Havens

Collection of utility functions
"""

import numpy as np
import pandas as pd
from datetime import datetime
import pytz
import os
from smrf.utils import io
from shutil import copyfile
from .gitinfo import __gitVersion__, __gitPath__
from smrf import __version__, __core_config__
import random


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
        tuple:
            **dd** - decimal day from start of water year
            **wy** - Water year

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

    Args:
        data: Pandas dataframe containing the station data
        config: The config object produced by :fun
    """
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
        raise ValueError("Developer Micah_o was unsure how to handle this scenario... please advise")

    # Output station data to CSV
    csv_var = ['metadata', 'air_temp', 'vapor_pressure','precip','wind_speed','wind_direction','cloud_factor']
    for k in csv_var:
        fname = os.path.join(backup_dir,k+'.csv')
        v = getattr(data,k)
        v.to_csv(fname)

        #Adjust and output the inifile
        config['csv'][k] = fname

    #Copy topo files over to backup
    ignore = ['basin_lon','basin_lat','type']
    for s in config['topo']:
        src = config['topo'][s]
        if s not in ignore and src != None:
            dst =  os.path.join(backup_dir,os.path.basename(src))
            config["topo"][s] = dst
            copyfile(src, dst)

    #We dont want to backup the backup
    config['output']['input_backup'] = False
    #output inifile
    io.generate_config(config,os.path.join(backup_dir,'backup_config.ini'))

def getgitinfo():
    """gitignored file that contains specific SMRF version and path

    Input:
        - none
    Output:
        - path to base SMRF directory
        - git version from 'git describe'
    """
    # return git describe if in git tracked SMRF
    if len(__gitVersion__) > 1:
        return __gitVersion__

    # return overarching version if not in git tracked SMRF
    else:
        version = 'v'+__version__
        return version

def getConfigHeader():
    cfg_str = ("Config File for SMRF {0}\n"
              "For more SMRF related help see:\n"
              "{1}").format(getgitinfo(),'http://smrf.readthedocs.io/en/latest/')
    return cfg_str


def config_documentation():
    """
    Auto documents the core config file. Creates a file named auto_config.rst
    in the docs folder which is then used for documentation.
    """

    mcfg = io.get_master_config()

    #RST header
    config_doc ="Config File Reference\n"
    config_doc+="=====================\n"
    config_doc+="""Below are the sections and items that are registered to the
configuration file. If an entry conflicts with these SMRF will end
the run and show the errors with the config file. If an entry is not provided
SMRF will automatical add the default in.
"""

    #Sections
    for section in mcfg.keys():
        #Section header
        config_doc+=" \n"
        config_doc += "{0}\n".format(section)
        config_doc += "-"*len(section)+'\n'
        #If distributed module link api
        dist_modules = ['air_temp','vapor_pressure','precip','wind', 'albedo','thermal','solar','soil_temp']
        if section == 'precip':
            sec = 'precipitation'
        else:
            sec = section
        if section in dist_modules:
            intro = """
The {0} section controls all the available parameters that effect
the distribution of the {0} module, espcially  the associated models.
For more detailed information please see :mod:`smrf.distribute.{0}`.
            """.format(sec)
        else:
            intro = """
The {0} section controls the {0} parameters for an entire SMRF run.
            """.format(sec)

        config_doc+=intro
        config_doc+="\n"

        #Auto document config file according to master config contents
        for item,v in sorted(mcfg[section].items()):
            #Check for attributes that are lists
            for att in ['default','options']:
                z = getattr(v,att)
                if type(z) == list:
                    combo = ' '
                    doc_s = combo.join([str(s) for s in z])
                    setattr(v,att,doc_s)

            #Bold item with definition
            config_doc+="| **{0}**\n".format(item)

            #Add the item description
            config_doc+="| \t{0}\n".format(v.description)

            #Default
            config_doc+="| \t\t*Default: {0}*\n".format(v.default)

            #Add expected type
            config_doc+="| \t\t*Type: {0}*\n".format(v.type)

            #Print options should they be available
            if v.options:
                config_doc+="| \t\t*Options:*\n *{0}*\n".format(v.options)

            config_doc+="| \n"

            config_doc+="\n"

    path = os.path.abspath('./')
    path = os.path.join(path,'auto_config.rst')
    print("Writing auto documentation for config file to:\n{0}".format(path))
    with open(path,'w+') as f:
        f.writelines(config_doc)
    f.close()

def check_station_colocation(metadata_csv=None,metadata=None):
    """
    Takes in a data frame representing the metadata for the weather stations
    as produced by :mod:`smrf.framework.model_framework.SMRF.loadData` and
    check to see if any stations have the same location.

    Args:
        metadata_csv: CSV containing the metdata for weather stations
        metadata: Pandas Dataframe containing the metdata for weather stations

    Returns:
        repeat_sta: list of station primary_id that are colocated
    """
    if metadata_csv != None:
        metadata = pd.read_csv(metadata_csv)
        metadata.set_index('primary_id', inplace=True)

    #Unique station locations
    unique_x = list(metadata.xi.unique())
    unique_y = list(metadata.yi.unique())

    repeat_sta = []

    #Cycle through all the positions look for multiple  stations at a position
    for x in unique_x:
        for y in unique_y:
            x_search = metadata['xi'] == x
            y_search = metadata['yi'] == y
            stations = metadata.index[x_search & y_search].tolist()

            if len(stations) > 1:
                repeat_sta.append(stations)

    if len(repeat_sta) == 0:
        repeat_sta = None

    return repeat_sta


def getqotw():
    p = os.path.dirname(__core_config__)
    q_f = os.path.abspath(os.path.join('{0}'.format(p),'.qotw'))
    with open(q_f) as f:
        qs = f.readlines()
        f.close()
    i = random.randrange(0,len(qs))
    return qs[i]
