from smrf.utils.io import read_config

def parse_str_setting(str_option):
    """
    Parses a single string where options are separated by =
    returns tuple of string
    """
    if "=" in str_option:
        name,option = str_option.split("=")
        name = (name.lower()).strip()
        option = (option.lower()).strip()
    else:
        raise ValueError("Config file string does not have options with = to parse.")

    return name,option

def parse_lst_options(option_lst_str):
    """
    parse options that can be lists form the config file and returns a dict
    e.g.
    available_options = distribution=[idw,dk,grid],slope=[-1,0,1]...
    returns
    available_options_dict = {"distribution":[dk,grid,idw],
              "slope":[-1,0,1]}
    """
    available = {}
    #check to see if it is a lists
    print option_lst_str
    if option_lst_str is not None:
        if type(option_lst_str) != list:
            options_parseable = [option_lst_str]
        else:
            options_parseable = option_lst_str
        for entry in options_parseable:
            name,option_lst = parse_str_setting(entry)
            if '[' in option_lst and " " in option_lst:
                options = (''.join(c for c in option_lst if c not in '[]')).split(" ")

            else:
                options = option_lst

            available[name] = options

    return available

def check_config_file(user_config_fname, control_fname):

    config = read_config(control_fname)

    users_cfg = read_config(user_config_fname)
    errors = []
    #Compare user config file to our master config
    for section,configured in users_cfg.items():
        print "section = {0}".format(section)
        #Are these valid sections?
        if section not in config.keys():
            errors.append("Section {0} is not a valid section in smrf config files".format(section))

        #Parse the possible options
        else:
            available =  parse_lst_options(config[section]['available_options'])
            print "Available Options = {0}".format(available)
        #In the section check the values and options
        for item,value in configured.items():
            #Is the item known as a configurable
            if item in config[section]["configurable"]:
                if item in available.keys():
                    if value not in available[item]:
                        errors.append("Value {0} is not a valid option for item {1} in section {2}.".format(value,item,section))
            else:
                errors.append("Section: {0}, item {1} is not a configurable item in smrf config files.".format(section,item))

    print "Configuration Status Report:"
    print "="*100
    for e in errors:
        print e
if __name__ == "__main__":
    check_config_file('./test_data/testConfig.ini','./smrf/framework/CoreConfig.ini')
