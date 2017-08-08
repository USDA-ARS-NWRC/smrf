#!/usr/bin/env python

from smrf.utils import io
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Examines SMRF config files for issues.')
    parser.add_argument('config_file', metavar='F', type=str,
                        help='Path to SMRF config file that needs checking')
    parser.add_argument('-w', dest='write', action='store_true',
                        help='Determines whether to write out the file with all the defaults')
    args = parser.parse_args()

    if os.path.isfile(args.config_file):
        user_cfg = io.read_config(args.config_file)
        config = io.get_master_config()
        user_cfg = io.add_defaults(user_cfg,config)
        warnings, errors = io.check_config_file(user_cfg,config)
        io.print_config_report(warnings,errors)
    else:
        raise IOError('File does not exist.')

    if args.write:
        out_f = './{0}_full.ini'.format(os.path.basename(args.config_file).split('.')[0])
        print("Writing complete config file showing all defaults of values that were not provided...")
        print('{0}'.format(out_f))
        io.generate_config(user_cfg,out_f)

if __name__ == '__main__':
    main()
