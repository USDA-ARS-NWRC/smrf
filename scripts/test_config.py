from smrf.utils.io import read_config, read_master_config, check_config_file, add_defaults
import subprocess
import smrf
from datetime import date
import sys

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
