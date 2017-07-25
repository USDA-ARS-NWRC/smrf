from smrf.utils.io import read_config
import subprocess
import smrf
def generate_config(config):
    """
    Generates a list of strings to be written in the ini file
    """
    #Header surround each commented titles in the ini file
    section_header = ('#'*80) + '\n' + ('# {0}\n') +('#'*80)

    #Dictionaries do not go in order so we provide the order here
    order_lst = ['topo',
                  'time',
                  'stations',
                  'air_temp',
                  'vapor_pressure',
                  'wind',
                  'precip',
                  'albedo',
                  'solar',
                  'thermal',
                  'soil_temp',
                  'logging',
                  'system'
                  ]


    #Dictionary of commented sectino titles
    titles = {'topo': "Files for DEM and vegetation",
                  'time': "Dates to run model",
                  'stations': "Stations to use",
                  'air_temp': "Air temperature distribution",
                  'vapor_pressure': "Vapor pressure distribution",
                  'wind': "Wind speed and wind direction distribution",
                  'precip': "Precipitation distribution",
                  'albedo': "Albedo distribution",
                  'solar': "Solar radiation distribution",
                  'thermal': "Thermal radiation distribution",
                  'soil_temp': " Soil temperature",
                  'logging': "Logging",
                  'system': "System variables"
                  }

    label = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])

    #Construct the str
    config_str="#"*80
    config_str += """
#
# Configuration file for SMRF V{0}
# git commit hash: {1}
# For details on configuration syntax see:
# https://docs.python.org/2/library/configparser.html
#
# Configuration files may include comments, prefixed by specific characters
# (# and ;). Comments may appear on their own in an otherwise empty line, or
# may be entered in lines holding values or section names. In the latter case,
# they need to be preceded by a whitespace character to be recognized as a
# comment. (For backwards compatibility, only ; starts an inline comment,
# while # does not.)
""".format(smrf.__version__,label)
    for section in order_lst:
        #Add the header
        config_str+='\n'*2
        config_str+=section_header.format(titles[section])
        config_str+='\n'
        config_str+='\n[{0}]\n'.format(section)
        #Add section items and values
        for k,v in config.get(section).items():
            config_str+="{0:<30} {1:<10}\n".format((k+':'),v)

    print config_str


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

def check_config_file(user_cfg, config):
    """
    looks at the users provided config file and checks it to a master config file
    looking at correctness and missing info.
    """

    print "\nChecking config file for issues..."
    errors = []
    warnings = []
    msg = "{: >10} {: >25} {: >60}"

    #Compare user config file to our master config
    for section,configured in user_cfg.items():
        #Are these valid sections?
        if section not in config.keys():
            errors.append(msg.format(section,item, "Not a valid section."))

        #Parse the possible options
        else:
            available =  parse_lst_options(config[section]['available_options'])

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

def test_process(user_config_fname,control_fname):
    user_cfg = read_config(user_config_fname)
    config = read_config(control_fname)
    check_config_file(user_cfg,config)
    generate_config(user_cfg)

if __name__ == "__main__":
    test_process('./test_data/testConfig.ini','./smrf/framework/CoreConfig.ini')
