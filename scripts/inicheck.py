#!/usr/bin/env python

from smrf.utils import io
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Examines SMRF config files for issues.')
    parser.add_argument('config_file', metavar='F', type=str,
                        help='Path to SMRF config file that needs checking')
    parser.add_argument('--write', dest='write', action='store_true',
                        help='Determines whether to write out the file with all the defaults')
    args = parser.parse_args()

    if os.path.isfile(args.config_file):
        user_cfg = io.read_config(args.config_file)
        config = io.get_master_config()
        user_cfg = io.add_defaults(user_cfg,config)
        warnings, errors = io.check_config_file(user_cfg,config)
        io.print_config_report(warnings,errors)
    else:
        raise

if __name__ == '__main__':
    main()
