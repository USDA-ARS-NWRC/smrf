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

def check_config_file(user_config_fname, control_fname):

    config = read_config(control_fname)

    users_cfg = read_config(user_config_fname)
    errors = []
    warnings = []
    msg = "{: >10} {: >25} {: >60}"

    #Compare user config file to our master config
    for section,configured in users_cfg.items():
        #Are these valid sections?
        if section not in config.keys():
            errors.append(msg.format(section,item, "Not a valid section."))

        #Parse the possible options
        else:
            available =  parse_lst_options(config[section]['available_options'])
            print available
        #In the section check the values and options
        for item,value in configured.items():
            #Did the user provide a list value
            if type(value) != list:
                val_lst = [value]
            else:
                val_lst = value

            for v in val_lst:
                #Is the item known as a configurable item
                if item in config[section]["configurable"]:
                    #Are there known options for this item
                    if item in available.keys():
                        print section,item,value,v

                        if str(v).lower() not in available[item]:
                            warn_str = "Caution: Unable to check {0} against anything".format(item)
                            errors.append(msg.format(section,item, warn_str))
                else:
                    warnings.append(msg.format(section,item, "Unable to confirm item. Common for wind section."))

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

if __name__ == "__main__":
    check_config_file('./test_data/testConfig.ini','./smrf/framework/CoreConfig.ini')
    check_config_file('./test_data/testConfig.ini','./smrf/framework/CoreConfig.ini')
