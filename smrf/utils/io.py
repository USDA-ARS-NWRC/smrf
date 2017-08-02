#!/usr/bin/env python
"""Input/Output functions

Adapted from the UW-Hydro tonic project
"""

import os
from collections import Sequence
from .pycompat import OrderedDict, SafeConfigParser, basestring, unicode_type

__version__ = "0.2.2"

def parse_str_setting(str_option):
    """
    Parses a single string where options are separated by =
    returns tuple of string
    Require users specfies settings with an equals sign
    """

    if "=" in str_option:
        name,option = str_option.split("=")
        name = (name.lower()).strip()
        option = (option.lower()).strip()

    else:
        msg = "Config file string does not have any options with = to parse."
        msg+= "\nError occurred parsing:\n {0}".format(str_option)
        raise ValueError(msg)

    return name,option


def parse_lst_options(option_lst_str):
    """
    Parse options that can be lists form the master config file and returns a dict
    e.g.
    available_options = distribution=[idw,dk,grid],slope=[-1 0 1]...
    returns
    available_options_dict = {"distribution":[dk grid idw],
              "slope":[-1 0 1]}
    """
    available = {}
    #check to see if it is a lists
    if option_lst_str is not None:
        if type(option_lst_str) != list:
            options_parseable = [option_lst_str]
        else:
            options_parseable = option_lst_str

        for entry in options_parseable:
            name,option_lst = parse_str_setting(entry)

            if '[' in option_lst and " " in option_lst:
                #Account for special syntax for providing a list answer
                options = (''.join(c for c in option_lst if c not in '[]'))
                options = (options.replace('\n'," ")).split(' ')
            else:
                options = option_lst

            available[name] = options

    return available


def check_config_file(user_cfg, master_config):
    """
    looks at the users provided config file and checks it to a master config file
    looking at correctness and missing info.
    """

    print "\nChecking config file for issues..."
    errors = []
    warnings = []
    msg = "{: <20} {: <30} {: <60}"

    #Compare user config file to our master config
    for section,configured in user_cfg.items():
        #Are these valid sections?
        if section not in master_config.keys():
            errors.append(msg.format(section,item, "Not a valid section."))

        #Parse the possible options
        else:
            available =  master_config[section]['available_options']

        #In the section check the values and options
        for item,value in configured.items():
            #Did the user provide a list value or single value
            if type(value) != list:
                val_lst = [value]
            else:
                val_lst = value

            for v in val_lst:
                #Is the item known as a configurable item
                if item in master_config[section]["configurable"]:
                    #Are there known options for this item
                    if item in available.keys():
                        v_str = str(v).lower()
                        if v_str not in available[item]:
                            err_str = "Invalid option: {0} ".format(str(v))
                            err_str+="\n available_options were {0}".format(available[item])
                            errors.append(msg.format(section,item, err_str))
                else:
                    wrn = "Not a registered option."
                    if section.lower() == 'wind':
                        wrn +=  " Common for station names."

                    warnings.append(msg.format(section,item, wrn))

    msg_len = 110
    print "\n"*2
    print "Configuration Status Report:"
    print "="*msg_len
    if len(warnings)>0:
        print "WARNINGS:"
        print msg.format("Section","Item", "Message")
        print "_"*msg_len
        for w in warnings:
            print w
        print "\n"

    if len(errors)>0:
        print "ERRORS:"
        print msg.format("Section","Item", "Message")
        print "_"*msg_len
        for e in errors:
            print e
        print "\n"

def add_defaults(user_config,master_config):
    """
    Look through the users config file and section by section add in missing
    parameters to add defaults
    """
    print "\nAdding default values to config file..."
    for section,configured in user_config.items():
            for k,v in master_config[section]["defaults"].items():
                if k not in configured.keys():
                    user_config[section][k]=v
    return user_config

# -------------------------------------------------------------------- #
def read_config(config_file, default_config=None):
    """
    Return a dictionary with subdictionaries of all configFile options/values
    """
    config = SafeConfigParser()
    config.optionxform = str
    config.read(config_file)
    sections = config.sections()
    dict1 = OrderedDict()
    for section in sections:
        options = config.options(section)
        dict2 = OrderedDict()
        for option in options:
            dict2[option.lower()] = config_type(config.get(section, option))
        dict1[section.lower()] = dict2

    if default_config is not None:
        for name, section in dict1.items():
            if name in default_config.keys():
                for option, key in default_config[name].items():
                    if option not in section.keys():
                        dict1[name][option] = key

    return dict1


def read_master_config(master_config_file):
    config = read_config(master_config_file)
    sections = config.keys()
    for section in sections:
        config[section]["available_options"] =  parse_lst_options(config[section]['available_options'])
        config[section]["defaults"] =  parse_lst_options(config[section]['defaults'])

    return config

# -------------------------------------------------------------------- #
def type_configobj(d):
    """recursively loop through dictionary calling config_type"""
    for k, v in d.items():
        if isinstance(v, dict):
            type_configobj(v)
        else:
            d[k] = config_type(v)
    return d
# -------------------------------------------------------------------- #


# -------------------------------------------------------------------- #
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

# -------------------------------------------------------------------- #


# -------------------------------------------------------------------- #
def isfloat(x):
    '''Test if value is a float'''
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True
# -------------------------------------------------------------------- #


# -------------------------------------------------------------------- #
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
# -------------------------------------------------------------------- #


# -------------------------------------------------------------------- #
def isscalar(x):
    '''Test if a value is a scalar'''
    if isinstance(x, (Sequence, basestring, unicode_type)):
        return False
    else:
        return True
# -------------------------------------------------------------------- #
