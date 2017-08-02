from smrf.utils.io import read_config, read_master_config, check_config_file, add_defaults
import subprocess
import smrf
from datetime import date
import sys


def generate_config(config,fname):
    """
    Generates a list of strings to be written in the ini file
    """
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
# Configuration file for SMRF V{0}
# Git commit hash: {1}
# Date generated: {2}
#
# For details on configuration file syntax see:
# https://docs.python.org/2/library/configparser.html
#
# For more SMRF related help see:
# http://smrf.readthedocs.io/en/latest/

""".format(smrf.__version__,smrf.__gitHash__, date.today())

    #Check for one of the three data set options
    user_sections = config.keys()
    if 'csv' in user_sections:
        order_lst.remove('mysql')
        order_lst.remove('gridded')

    elif 'mysql' in user_sections:
        order_lst.remove('csv')
        order_lst.remove('gridded')

    elif 'girdded' in user_sections:
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

    #print config_str
    with open(fname,'w') as f:
        f.writelines(config_str)
        f.close()


def test_process(user_config_fname,control_fname):
    user_cfg = read_config(user_config_fname)
    config = read_master_config(control_fname)
    user_cfg = add_defaults(user_cfg,config)
    check_config_file(user_cfg,config)
    generate_config(user_cfg,'./fuke.ini')


if __name__ == "__main__":
    user_f = sys.argv[1]
    test_process(user_f,'./smrf/framework/CoreConfig.ini')
    #test_process('./fuke.ini','./smrf/framework/CoreConfig.ini')
