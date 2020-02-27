#!/usr/bin/env python3

import argparse

from smrf.framework.model_framework import run_smrf
from smrf.utils.utils import handle_run_script_options


def argument_parser():
    parser = argparse.ArgumentParser(
        description='Examines SMRF config files for issues.'
    )
    parser.add_argument(
        'config_file',
        metavar='file',
        type=str,
        help='Path to SMRF config file to run or to a directory containing one'
    )

    return parser


def run():
    """
    run_smrf is a command line program meant to take a single
    argument for the config file.  From this program, smrf.framework
    will be loaded to run the full program.

    Users can also run the model as they want by using the smrf.framework.SMRF
    class to change things or whatever
    """

    args = argument_parser().parse_args()
    config_file = handle_run_script_options(args.config_file)
    run_smrf(config_file)


if __name__ == '__main__':
    run()
