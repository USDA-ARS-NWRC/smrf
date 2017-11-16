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
#Python 3 troubles and hack
if sys.version_info[0] >= 3:
    from ..utils import utils
else:
    import utils

from .pycompat import OrderedDict, SafeConfigParser, basestring, unicode_type
from datetime import date
import pytz
import pandas as pd


class MasterConfig():
    def __init__(self,filename):
        self.cfg = self._read_master_config(filename)

    def _read_master_config(self, master_config_file):
        """
        Reads in the core config file which has special syntax for specifying options

        Args:
            master_config_file: String path to the master config file.

        Returns:
            config: Dictionary of dictionaries representing the defaults and available
                    options in SMRF. Based on the Core Config file.
        """

        cfg = {}
        #Read in will automatically get the configurable key added
        raw_config = read_config(master_config_file)
        for section in raw_config.keys():
            sec = {}
            for item in raw_config[section]:
                sec[item] = ConfigEntry(name = item, parseable_line=raw_config[section][item])

            cfg[section] = sec

        return cfg


class ConfigEntry():
    def __init__(self, name=None, value=None, default = None, entry_type='str', options=[], parseable_line=None):
        self.name = name
        self.value = value
        self.default = default
        self.options = options
        self.description = ''
        self.type = entry_type

        if parseable_line != None:
            self.parse_info(parseable_line)

        self.default = self.convert_type(self.default)

        self.options = self.convert_type(self.options)

        #Options should always be a list
        if type(self.options) != list:
            self.options = [self.options]

    def parse_info(self,info):
        """
        """
        if type(info) != list:
            info = [info]

        for s in info:
            if '=' in s:
                a = s.split('=')
            else:
                raise ValueError('Master Config file missing an equals sign in entry {0}\n or missing a comma above this entry'.format(info))

            name = (a[0].lower()).strip()
            if not hasattr(self,name):
                raise ValueError("Invalid option set in the Master Config File for item ----->{0}".format(name))

            value = a[1].strip()

            result = []
            value = value.replace('\n'," ")
            value = value.replace('\t',"")

            # Is there a list?
            if '[' in value:
                if ']' not in value:
                    raise ValueError("Missing bracket in Master Config file under {0}".format(name))
                else:
                    value = (''.join(c for c in value if c not in '[]'))
                    value = value.split(' ')
                    #value = [v for v in value if v == ' ' ]

            result = value
            setattr(self,name,result)


    def convert_type(self,value):
        if str(value).lower() == 'none':
            value = None

        else:
            if self.type not in str(type(value)):
                value = cast_variable(value,self.type)

        return value

def cast_variable(variable,type_value):
    """
    Casts an object to the spectified type value
    Args:
        variable - some variable to be casted
        type_value - string value indicating type to cast.
    Returns:
        value - The original variable now casted in type_value
    """
    if type(variable) != list:
        variable = [variable]
    type_value = str(type_value)
    value = []
    for v in variable:
        if 'datetime' in type_value:
            value.append(pd.to_datetime(v))
        elif 'bool' in type_value:
            if v.lower() in ['yes','y','true']:
                v = True
            elif v.lower() in ['no','n','false']:
                v = False

            value.append(bool(v))
        elif 'int' in type_value:
            value.append(int(v))
        elif 'float' in type_value:
            value.append(float(v))
        elif type_value == 'filename' or type_value == 'directory':
            value.append(v)
        elif v in ['none']:  # None
            value.append(None)
        elif 'str' in type_value:
            value.append(str(v.lower()))
        else:
            raise ValueError("Unknown type_value prescribed. ----> {0}".format(type_value))

    if len(value) == 1:
        value = value[0]
    return value


def parse_config_type(options):
    """
    Parses out the type of a config file available options entry, types are identified
    by < > and type string is the default.
    Types parseable
    datetime
    bool
    integer
    float
    str
    filename
    directory

    Args:
        options - Parsed lines from the master config file.

    Returns:
        tuple:
            Returns the type and the rest of the line in the config file.
            - **option_type** - the string name of the expected type.
            - **option** - the string value of the option parsed.

    """

    type_options = ['datetime','filename','directory','bool','int','float','str']
    if '<' in options and '>' in options:
        start = options.index('<')
        end = options.index('>')
        option_type = options[start+1:end]
        option = options[end+1:]
    else:
        option_type='str'
        option = options

    #Recognize the options.
    if option_type in type_options:
        #print option_type, option
        return option_type, option

    else:
        raise ValueError("Unrecognized type in CoreConfig file ---> '{0}'".format(options))


def parse_str_setting(str_option):
    """
    Parses a single string where options are separated by =
    returns tuple of string
    Require users specfies settings with an equals sign

    Args:
        str_option - the string line that was received from the config file

    Returns:
        tuple:
            Returns the name and values parsed in the config file.
            - **name** - the string name value of the option parsed.
            - **option** - the string value of the option parsed.
    """

    if "=" in str_option:
        name,option = str_option.split("=")
        name = (name.lower()).strip()
        option = (option.lower()).strip()
        option_type, option = parse_config_type(option)
    else:
        msg = "Config file string does not have any options with = to parse."
        msg+= "\nError occurred parsing in config file:\n {0}".format(str_option)
        raise ValueError(msg)

    return name,option_type,option


def parse_lst_options(option_lst_str,types=False):
    """
    Parse options that can be lists form the master config file and returns a dict
    e.g.
    available_options = distribution=[idw,dk,grid],slope=[-1 0 1]...
    returns
    available_options_dict = {"distribution":[dk grid idw],
              "slope":[-1 0 1]}

    Args:
        option_lst_str -  string value of the lined parsed potentiall containing a list.

    Returns:
        available: A dictionary with keys as the names of the entries and values are lists of the options

    """

    available = {}
    #check to see if it is a lists
    if option_lst_str is not None:
        if type(option_lst_str) != list:
            #account for auto lists made by config parser
            options_parseable = [option_lst_str]
        else:
            options_parseable = option_lst_str

        for entry in options_parseable:
            name,option_type,option_lst = parse_str_setting(entry)

            #Account for special syntax for providing a list answer
            options = (''.join(c for c in option_lst if c not in '[]'))
            options = (options.replace('\n'," ")).split(' ')
            if type(options)!=list:
                options = [option_lst]

            #Get correct data type
            for i,o in enumerate(options):
                if o:
                    value = cast_variable(o,option_type)
                else:
                    value = ""
                options[i] = value

            #Change it back from being a list
            if len(options) == 1:
                options = options[0]
            if types:
                available[name] = ConfigEntry(name=name, entry_type = option_type, available_options = options)
            else:
                available[name] = ConfigEntry(name=name, available_options = options)

    return available


def check_config_file(user_cfg, master_config,user_cfg_path=None):
    """
    looks at the users provided config file and checks it to a master config file
    looking at correctness and missing info.

    Args:
        user_cfg - Config file dictionary created by :func:`~smrf.utils.io.read_config'.
        master_config - Config file dictionary created by :func:`~smrf.utils.io.read_master_config'
        user_cfg_path - Path to the config file that is being checked. Useful for relative file paths. If none assumes relative paths from CWD.

    Returns:
        tuple:
        - **warnings** - Returns a list of string messages that are consider non-critical issues with config file.

        - **errors** - Returns a list of string messages that are consider critical issues with the config file.
    """

    msg = "{: <20} {: <30} {: <60}"
    errors = []
    warnings = []

    #Check for all the required sections
    has_a_data_section = False
    data_sections = ['csv',"mysql","gridded"]
    user_sections = user_cfg.keys()

    for section in master_config.keys():
        if section not in user_sections and section not in data_sections:
            # stations not needed if gridded input data used
            if 'gridded' not in user_sections and section == 'stations':
                err_str = "Missing required section."
                errors.append(msg.format(section," ", err_str))

        #Check for a data section
        elif section in user_sections and section in data_sections:
            has_a_data_section = True

    if not has_a_data_section:
        err_str = "Must specify a CSV or MySQL or Gridded section."
        errors.append(msg.format(" "," ", err_str))

    #Compare user config file to our master config
    for section,configured in user_cfg.items():
        #Are these valid sections?
        if section not in master_config.keys():
            errors.append(msg.format(section,item, "Not a valid section."))

        #In the section check the values and options
        for item,value in configured.items():
            litem = item.lower()
            #Is the item known as a configurable item?
            if litem not in master_config[section].keys():
                wrn = "Not a registered option."
                if section.lower() == 'wind':
                    wrn +=  " Common for station names."
                warnings.append(msg.format(section,item, wrn))
            else:
                if litem != 'stations':
                    #Did the user provide a list value or single value
                    if type(value) != list:
                        val_lst = [value]
                    else:
                        val_lst = value

                    for v in val_lst:
                        if v != None:
                            v = master_config[section][litem].convert_type(v)
                            # Do we have an idea os what to expect (type and options)?
                            options_type = master_config[section][item].type

                            if options_type == 'datetime':
                                try:
                                    pd.to_datetime(v)
                                except:
                                    errors.append(msg.format(section,item,'Format not datetime'))

                            elif options_type == 'filename':
                                if user_cfg_path != None:
                                    p = os.path.split(user_cfg_path)
                                    v = os.path.join(p[0],v)

                                if not os.path.isfile(os.path.abspath(v)):
                                    errors.append(msg.format(section,item,'Path does not exist'))

                            elif options_type == 'directory':
                                if user_cfg_path != None:
                                    p = os.path.split(user_cfg_path)
                                    v = os.path.join(p[0],v)

                                if not os.path.isdir(os.path.abspath(v)):
                                    warnings.append(msg.format(section,item,'Directory does not exist'))

                            #Check int, bools, float
                            elif options_type not in str(type(v)):
                                errors.append(msg.format(section,item,'Expecting a {0} recieved {1}'.format(options_type,type(v))))

                            if master_config[section][item].options and v not in master_config[section][item].options:
                                err_str = "Invalid option: {0} ".format(v)
                                errors.append(msg.format(section, item, err_str))

    return warnings,errors


def print_config_report(warnings, errors, logger= None):
    """
    Pass in the list of string messages generated by check_config file.
    print out in a pretty format the issues

    Args:
        warnings - List of non-critical messages returned from :func:`~smrf.utils.io.check_config'.
        errors - List of critical messages returned from :func:`~smrf.utils.io.check_config'.
        logger - pass in the logger function being used. If no logger is provided, print is used. Default = None

    Returns:
        None
    """

    msg = "{: <20} {: <25} {: <60}"

    #Check to see if user wants the logger or stdout
    if logger != None:
        out = logger.info
    else:
        out = print


    msg_len = 110
    out(" ")
    out(" ")
    out("Configuration File Status Report:")
    header = "="*msg_len
    out(header)
    any_warnings = False
    any_errors = False

    #Output warnings
    if len(warnings)>0:
        any_warnings=True
        out("WARNINGS:")
        out(" ")
        out(msg.format(" Section","Item", "Message"))
        out("-"*msg_len)
        for w in warnings:
            out(w)
        out(" ")
        out(" ")

    #Output errors
    if len(errors)>0:
        any_errors=True
        out("ERRORS:")
        out(" ")
        out(msg.format("Section","Item", "Message"))
        out("-"*msg_len)
        for e in errors:
            out(e)
        out(" ")
        out(" ")

    if not any_errors and not any_warnings:
        out("No errors or warnings were reported with the config file.\n")


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


def generate_config(config,fname, inicheck = False):
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
        order_lst.remove('mysql')
        order_lst.remove('gridded')

    elif 'mysql' in user_sections:
        order_lst.remove('csv')
        order_lst.remove('gridded')

    elif 'gridded' in user_sections:
        order_lst.remove('stations')
        order_lst.remove('csv')
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


def read_config(config_file, encoding='utf-8'):
    """
    Returns a dictionary with subdictionaries of all configFile options/values

    Args:
        config_file - String path to the config file to be opened.

    Returns:
        dict1: A dictionary of dictionaires representing the config file.
    """

    config = SafeConfigParser()
    config.optionxform = str


    PY3 = sys.version_info[0] >= 3

    if PY3:
        config.read(config_file, encoding=encoding)
    else:
        config.read(config_file)

    sections = config.sections()
    dict1 = OrderedDict()
    for section in sections:
        options = config.options(section)
        dict2 = OrderedDict()
        for option in options:
            dict2[option.lower()] = config_type(config.get(section, option))
        dict1[section.lower()] = dict2

    return dict1


def get_master_config():
    """
    Returns the master config file dictionary
    """
    cfg = MasterConfig(__core_config__).cfg
    return cfg


def update_config_paths(cfg,user_cfg_path, mcfg = None):
    """
    Paths should always be relative to the config file or
    absolute.
    """
    if mcfg == None:
        mcfg = get_master_config()
    #Cycle thru users config
    for section in cfg.keys():
        for item in cfg[section].keys():
            d = cfg[section][item]
            #Does master have this and is it not none
            if item in mcfg[section].keys() and d != None:
                m = mcfg[section][item]
                #Any paths
                if m.type == 'filename' or  m.type == 'directory':
                    if not os.path.isabs(cfg[section][item]):
                        path = os.path.abspath(os.path.join(os.path.split(user_cfg_path)[0],cfg[section][item]))
                        cfg[section][item] = path
    return cfg

def get_user_config(fname, mcfg = None):
    """
    Retrieve the user config and apply
    types according to the master config.

    Args:
        fname - filename of the user config file.
        mcfg - master config object
    Returns:
        cfg - A dictionary of dictionaries containing the config file
    """
    if mcfg == None:
        mcfg = get_master_config()

    cfg = read_config(fname)

    #Convert the types
    for section in cfg.keys():
        for item in cfg[section]:
            u = cfg[section][item]
            if item in mcfg[section]:
                m = mcfg[section][item]
                u = mcfg[section][item].convert_type(u)

                #If all is  requested then use all the options
                if u == 'all':
                    u = m.options
                    u.remove('all')

                #Check for stations and passwords
                if m.type == 'str' and u != None:
                    if type(u) == list:
                        if item =='stations':
                            u = [o.upper() for o in u]
                        else:
                            u = [o.lower() for o in u]

                    else:
                        if item != 'password':
                            u = u.lower()

                #Add the timezone to all date time
                elif mcfg[section][item].type == 'datetime' and u != None:
                    #We tried to apply this to all the datetimes but it was not working if we changed it for the start
                    # and end dates with mySQL.

                    if item not in ['start_date', 'end_date']:
                        u = u.replace(tzinfo = pytz.timezone(cfg['time']['time_zone']))


                cfg[section][item] = u

    return cfg


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
