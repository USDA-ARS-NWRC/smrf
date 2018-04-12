#!/usr/bin/env python
"""
Input/Output functions
Adapted from the UW-Hydro tonic project
"""
from __future__ import print_function

import os
from collections import Sequence
from smrf import __core_config__, __version__
import sys
# hack for install with either version 2 or version 3 python
if sys.version_info[0] >= 3:
    from smrf.utils import utils
else:
    import utils

from .pycompat import OrderedDict, SafeConfigParser, basestring, unicode_type
from datetime import date
import pytz
import pandas as pd




def add_defaults(user_config,master_config):
    """
    Look through the users config file and section by section add in missing
    parameters to add defaults

    Args:
        user_cfg - Config file dictionary created by :func:`~smrf.utils.io.read_config'.
        master_config - Config file dictionary created by :func:`~smrf.utils.io.read_master_config'

    Returns:
        user_cfg: User config dictionary with defaults added.
    """
    for section,configured in user_config.items():
            for k,v in master_config[section].items():
                if v.name not in configured.keys():
                    #print(v.name,v.default)
                    user_config[section][k]=v.default
    return user_config


def generate_config(config,fname, inicheck = False, order_lst = None, titles = None):
    """
    Generates a list of strings to be written and then writes them in the ini file

    Args:
        config - Config file dictionary created by :func:`~smrf.utils.io.read_config'.
        fname - String path to the output location for the new config file.
        inicheck - Boolean value that adds the line generated using inicheck to config, Default = False

    Returns:
        None
    """

    # find output of 'git describe'
    gitVersion = utils.getgitinfo()

    #Header surround each commented titles in the ini file
    section_header = ('#'*80) + '\n' + ('# {0}\n') +('#'*80)

    #Dictionaries do not go in order so we provide the order here
    if order_lst == None:
        order_lst = ['topo',
                      'time',
                      'stations',
                      'csv',
                      'mysql',
                      'gridded',
                      'air_temp',
                      'vapor_pressure',
                      'wind',
                      'precip',
                      'albedo',
                      'solar',
                      'thermal',
                      'soil_temp',
                      'output',
                      'logging',
                      'system'
                      ]

    #Dictionary of commented section titles
    if titles == None:
        titles = {'topo': "Files for DEM and vegetation",
                  'time': "Dates to run model",
                  'stations': "Stations to use",
                  'csv': "CSV data files",
                  'mysql': "MySQL database",
                  'gridded': "Gridded dataset i.e. wrf_out",
                  'air_temp': "Air temperature distribution",
                  'vapor_pressure': "Vapor pressure distribution",
                  'wind': "Wind speed and wind direction distribution",
                  'precip': "Precipitation distribution",
                  'albedo': "Albedo distribution",
                  'solar': "Solar radiation distribution",
                  'thermal': "Thermal radiation distribution",
                  'soil_temp': " Soil temperature",
                  'output': "Output variables",
                  'logging': "Logging",
                  'system': "System variables"
                }

    #Construct the section strings
    config_str="#"*80

    #File header
    config_str += """
#
# Configuration file for SMRF {0}
# Date generated: {1}
""".format(gitVersion, date.today())

    if inicheck:
        config_str+= "# Generated using: inicheck <filename> -w \n# "

    config_str+="""
# For details on configuration file syntax see:
# https://docs.python.org/2/library/configparser.html
#
# For more SMRF related help see:
# http://smrf.readthedocs.io/en/latest/
"""

    #Check for one of the three data set options
    user_sections = config.keys()
    if 'csv' in user_sections:
        if 'mysql' in order_lst:
            order_lst.remove('mysql')
        if 'gridded' in order_lst:
            order_lst.remove('gridded')

    elif 'mysql' in user_sections:
        if 'csv' in order_lst:
            order_lst.remove('csv')
        if 'gridded' in order_lst:
            order_lst.remove('gridded')

    elif 'gridded' in user_sections:
        if 'stations' in order_lst:
            order_lst.remove('stations')
        if 'csv' in order_lst:
            order_lst.remove('csv')
        if 'mysql' in order_lst:
            order_lst.remove('mysql')


    #Generate the string for the file, creating them in order.
    for section in order_lst:
        #Add the header
        config_str+='\n'*2
        config_str+=section_header.format(titles[section])
        config_str+='\n'
        config_str+='\n[{0}]\n'.format(section)
        #Add section items and values
        for k,v in config.get(section).items():
            if type(v) == list:
                astr = ", ".join(str(c.strip()) for c in v)
            else:
                astr = str(v)
            config_str+="{0:<30} {1:<10}\n".format((k+':'),astr)

    #Write out the string generated
    with open(os.path.abspath(fname),'w') as f:
        f.writelines(config_str)
        f.close()

def type_configobj(d):
    """recursively loop through dictionary calling config_type"""
    for k, v in d.items():
        if isinstance(v, dict):
            type_configobj(v)
        else:
            d[k] = config_type(v)
    return d


def config_type(value):
    """
    Parse the type of the configuration file option.
    First see the value is a bool, then try float, finally return a string.
    """
    if not isinstance(value, list):
        val_list = [x.strip() for x in value.split(',')]
    else:
        val_list = value
    ret_list = []

    for value in val_list:
        if value.lower() in ['true', 't']:  # True
            ret_list.append(True)
        elif value.lower() in ['false', 'f']:  # False
            ret_list.append(False)
        elif value.lower() in ['none', '']:  # None
            ret_list.append(None)
        elif isint(value):  # int
            ret_list.append(int(value))
        elif isfloat(value):  # float
            ret_list.append(float(value))
        else:  # string or similar
            ret_list.append(os.path.expandvars(value))

    if len(ret_list) > 1:
        return ret_list
    else:
        return ret_list[0]


def isbool(x):
    '''Test if str is an bolean'''
    if isinstance(x, float) or isinstance(x, basestring) and '.' in x:
        return False
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def isfloat(x):
    '''Test if value is a float'''
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def isint(x):
    '''Test if value is an integer'''
    if isinstance(x, float) or isinstance(x, basestring) and '.' in x:
        return False
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def isscalar(x):
    '''Test if a value is a scalar'''
    if isinstance(x, (Sequence, basestring, unicode_type)):
        return False
    else:
        return True
