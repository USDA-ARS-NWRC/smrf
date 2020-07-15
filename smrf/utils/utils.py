import copy
import os
import random
import sys
from datetime import datetime
from shutil import copyfile

import numpy as np
import pandas as pd
import pytz
import utm
from inicheck.checkers import CheckType
from inicheck.output import generate_config
from inicheck.utilities import mk_lst
from scipy.interpolate.interpnd import (CloughTocher2DInterpolator,
                                        LinearNDInterpolator)
from scipy.spatial import qhull as qhull

from smrf import __core_config__


class CheckStation(CheckType):
    """
    Custom check for ensuring our stations are always capitalized
    """

    def __init__(self, **kwargs):
        super(CheckStation, self).__init__(**kwargs)

    def type_func(self, value):
        """
        Attempt to convert all the values to upper case.

        Args:
            value: A single string in config entry representing a station name
        Returns:
            value: A single station name all upper case
        """

        return value.upper()


class CheckRawString(CheckType):
    """
    Custom `inicheck` checker that will not change the input string
    """

    def __init__(self, **kwargs):
        super(CheckRawString, self).__init__(**kwargs)

    def type_func(self, value):
        """
        Do not change the passed value at all
        Args:
            value: A single string
        Returns:
            value: A single string unchanged
        """

        return value


def find_configs(directory):
    """
    Searches through a directory and returns all the .ini fulll filenames.

    Args:
        directory: string path to directory.
    Returns:
        configs: list of paths pointing to the config file.
    """

    configs = []
    directory = os.path.abspath(os.path.expanduser(directory))

    for f in os.listdir(directory):
        if f.split('.')[-1] == 'ini':
            configs.append(os.path.join(directory, f))
    return configs


def handle_run_script_options(config_option):
    """
    Handle function for dealing with args in the SMRF run script

    Args:
        config_option: string path to a directory or a specific config file.
    Returns:
        configFile:Full path to an existing config file.
    """
    config_option = os.path.abspath(os.path.expanduser(config_option))

    # User passes a directory
    if os.path.isdir(config_option):
        configs = find_configs(config_option)

        if len(configs) > 1:
            print("\nError: Multiple config files detected in {0} please"
                  " ensure only one is in the folder.\n".format(config_option))
            sys.exit()

        else:
            configFile = configs[0]
    else:
        configFile = config_option

    if not os.path.isfile(configFile):
        print('\nError: Please provide a config file or a directory containing'
              ' one.\n')
        sys.exit()

    return configFile


def nan_helper(y):
    """
    Helper to handle indices and logical indices of NaNs.

    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])

    Args:
        y: 1d numpy array with possible NaNs

    Returns:
        tuple:
            **nans** - logical indices of NaNs
            **index** - a function

    """

    return np.isnan(y), lambda z: z.nonzero()[0]


def set_min_max(data, min_val, max_val):
    """
    Ensure that the data is in the bounds of min and max

    Args:
        data: numpy array of data to be min/maxed
        min_val: minimum threshold to trim data
        max_val: Maximum threshold to trim data

    Returns:
        data: numpy array of data trimmed at min_val and max_val
    """
    if max_val is None:
        max_val = np.inf
    if min_val is None:
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


def backup_input(data, config_obj):
    """
    Backs up input data files so a user can rerun a run with the exact data
    used for a run.

    Args:
        data: Pandas dataframe containing the station data
        config_obj: The config object produced by inicheck
    """
    # mask copy
    backup_config_obj = copy.deepcopy(config_obj)

    # Make the output dir
    backup_dir = os.path.join(backup_config_obj.cfg['output']['out_location'],
                              'input_backup')
    if not os.path.isdir(backup_dir):
        os.mkdir(backup_dir)

    # Check config file for csv section and remove alternate data form config
    if 'csv' not in backup_config_obj.cfg.keys():
        backup_config_obj.cfg['csv'] = {}
        # With a new section added, we need to remove the other data sections
        # backup_config_obj.apply_recipes()

    if 'stations' in backup_config_obj.cfg.keys():
        if 'client' in backup_config_obj.cfg['stations']:
            del backup_config_obj.cfg['stations']['client']

    # Output station data to CSV
    csv_var = ['metadata', 'air_temp', 'vapor_pressure', 'precip',
               'wind_speed', 'wind_direction', 'cloud_factor']

    for k in csv_var:
        fname = os.path.join(backup_dir, k + '.csv')
        v = getattr(data, k)
        v.to_csv(fname)

        # Adjust and output the inifile
        backup_config_obj.cfg['csv'][k] = fname

    # Copy topo files over to backup
    ignore = ['northern_hemisphere',
              'gradient_method', 'sky_view_factor_angles']
    for s in backup_config_obj.cfg['topo'].keys():
        src = backup_config_obj.cfg['topo'][s]
        # make not a list if lenth is 1
        if isinstance(src, list):
            src = mk_lst(src, unlst=True)
        # Avoid attempring to copy files that don't exist
        if s not in ignore and src is not None:
            dst = os.path.join(backup_dir, os.path.basename(src))
            backup_config_obj.cfg["topo"][s] = dst
            copyfile(src, dst)

    # We dont want to backup the backup
    backup_config_obj.cfg['output']['input_backup'] = False

    # Output inifile
    generate_config(backup_config_obj, os.path.join(
        backup_dir, 'backup_config.ini'))


def check_station_colocation(metadata_csv=None, metadata=None):
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
    if metadata_csv is not None:
        metadata = pd.read_csv(metadata_csv)
        metadata.set_index('primary_id', inplace=True)

    # Unique station locations
    unique_x = list(metadata.xi.unique())
    unique_y = list(metadata.yi.unique())

    repeat_sta = []

    # Cycle through all the positions look for multiple  stations at a position
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


def get_config_doc_section_hdr():
    """
    Returns the header dictionary for linking modules in smrf to the
    documentation generated by inicheck auto doc functions
    """
    hdr_dict = {}

    dist_modules = ['air_temp', 'vapor_pressure', 'precip', 'wind', 'albedo',
                    'thermal', 'solar', 'cloud_factor', 'soil_temp']

    for d in dist_modules:
        if d == 'precip':
            sec = 'precipitation'
        else:
            sec = d

        # If distributed module link api
        intro = ("The {0} section controls all the available parameters that"
                 " effect the distribution of the {0} module, espcially  the"
                 " associated models. For more detailed information please see"
                 " :mod:`smrf.distribute.{0}`\n").format(sec)

        hdr_dict[d] = intro

    return hdr_dict


def get_asc_stats(fp):
    """
    Returns header of ascii dem file
    """
    ts = {}
    header = {}

    ff = open(fp, 'r')
    for idl, line in enumerate(ff):
        tmp_line = line.strip().split()
        header[tmp_line[0]] = tmp_line[1]
        if idl >= 5:
            break
    ff.close()

    ts['nx'] = int(header['ncols'])
    ts['ny'] = int(header['nrows'])
    ts['du'] = float(header['cellsize'])
    ts['dv'] = float(header['cellsize'])
    ts['u'] = float(header['yllcorner'])
    ts['v'] = float(header['xllcorner'])

    ts['x'] = ts['v'] + ts['dv']*np.arange(ts['nx'])
    ts['y'] = ts['u'] + ts['du']*np.arange(ts['ny'])
    ts['y'] = ts['y'][::-1]

    # ASCII are lower left coordiante
    # must shift to cell center for interpolation
    ts['x'] = ts['x'] + ts['dv']/2
    ts['y'] = ts['y'] + ts['du']/2

    return ts


def getqotw():
    p = os.path.dirname(__core_config__)
    q_f = os.path.abspath(os.path.join('{0}'.format(p), '.qotw'))
    with open(q_f) as f:
        qs = f.readlines()
        f.close()
    i = random.randrange(0, len(qs))
    return qs[i]


def interp_weights(xy, uv, d=2):
    """
    Find vertices and weights of LINEAR interpolation for gridded interp.
    This routine follows the methods of scipy.interpolate.griddata as outlined
    here:
    https://stackoverflow.com/questions/20915502/speedup-scipy-griddata-for-multiple-interpolations-between-two-irregular-grids
    This function finds the vertices and weights which is the most
    computationally expensive part of the routine. The interpolateion can
    then be done quickly.

    Args:
        xy: n by 2 array of flattened meshgrid x and y coords of WindNinja grid
        uv: n by 2 array of flattened meshgrid x and y coords of SMRF grid
        d:  dimensions of array (i.e. 2 for our purposes)

    Returns:
        vertices:
        wts:

    """
    tri = qhull.Delaunay(xy)
    simplex = tri.find_simplex(uv)
    vertices = np.take(tri.simplices, simplex, axis=0)
    temp = np.take(tri.transform, simplex, axis=0)
    delta = uv - temp[:, d]
    bary = np.einsum('njk,nk->nj', temp[:, :d, :], delta)

    return vertices, np.hstack((bary, 1 - bary.sum(axis=1, keepdims=True)))


def grid_interpolate(values, vtx, wts, shp, fill_value=np.nan):
    """
    Broken out gridded interpolation from scipy.interpolate.griddata that takes
    the vertices and wts from interp_weights function

    Args:
        values: flattened WindNinja wind speeds
        vtx:    vertices for interpolation
        wts:    weights for interpolation
        shape:  shape of SMRF grid
        fill_value: value for extrapolated points

    Returns:
        ret:    interpolated values
    """
    ret = np.einsum('nj,nj->n', np.take(values, vtx), wts)
    ret[np.any(wts < 0, axis=1)] = fill_value

    ret = ret.reshape(shp[0], shp[1])

    return ret


def grid_interpolate_deconstructed(tri, values, grid_points, method='linear'):
    """
    Underlying methods from scipy grid_data broken out to pass in the tri
    values returned from qhull.Delaunay. This is done to improve the speed
    of using grid_data

    Args:
        tri:            values returned from qhull.Delaunay
        values:         values at HRRR stations generally
        grid_points:    tuple of vectors for X,Y coords of grid stations
        method:         either linear or cubic

    Returns:
        result of interpolation to gridded points
    """

    if method == 'cubic':
        return CloughTocher2DInterpolator(tri, values)(grid_points)
    elif method == 'linear':
        return LinearNDInterpolator(tri, values)(grid_points)


def apply_utm(s, force_zone_number):
    """
    Calculate the utm from lat/lon for a series

    Args:
        s: pandas series with fields latitude and longitude
        force_zone_number: default None, zone number to force to

    Returns:
        s: pandas series with fields 'X' and 'Y' filled
    """
    p = utm.from_latlon(s.latitude, s.longitude,
                        force_zone_number=force_zone_number)
    s['utm_x'] = p[0]
    s['utm_y'] = p[1]
    return s


def date_range(start_date, end_date, increment, timezone):
    """
    Calculate a list between start and end date with
    an increment
    """

    return list(pd.date_range(
        start_date,
        end_date,
        freq="{}min".format(increment),
        tz=timezone
    ))
