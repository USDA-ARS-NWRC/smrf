#!/usr/bin/env python3

import argparse
import os
from datetime import datetime

import netCDF4 as nc

from smrf.utils.wind.model import wind_model


def argument_parser():
    parser = argparse.ArgumentParser(
        description="Takes in Netcdf dem image and maxus file from "
                    "Adam Winstrals wind model. "
                    "The maxus file is required for SMRF simulations"
    )
    parser.add_argument(
        'dem',
        type=str,
        help='Netcdf file containing the dem'
    )
    parser.add_argument(
        '--out_maxus', '-O',
        metavar='OUTPUT_FILE',
        type=str,
        default='./maxus.nc',
        help='Output file path for maxus file'
    )
    parser.add_argument(
        '--increment', '-i',
        metavar='INCREMENT',
        type=int, default=5,
        help='Increment between direction calculations (degrees)'
    )
    parser.add_argument(
        '--sv_global', '-dmax',
        metavar='METER_VALUE',
        type=int,
        default=500,
        help='Length of outlying upwind search vector (meters)'
    )
    parser.add_argument(
        '--sv_local', '-l',
        metavar='METER_VALUE',
        type=int,
        default=100,
        help='Length of local upwind search vector (meters)'
    )
    parser.add_argument(
        '--height', '-H',
        metavar='METER_VALUE',
        type=int,
        default=3,
        help='Anemometer height in meters'
    )
    parser.add_argument(
        '--window', '-W',
        metavar='AVERAGE_VALUE',
        type=int,
        default=100,
        help='To average wind data across in the direction of the wind'
    )
    parser.add_argument(
        '--var_name', '-N',
        metavar='VARIABLE_NAME',
        type=str,
        default='dem',
        help='specify the variable name inside a netcdf file'
    )
    parser.add_argument(
        '--make_tbreak', '-tb',
        type=bool,
        default=False,
        help='Argument to make tbreak file that can be used for '
             'precipitation redistribution'
    )
    parser.add_argument(
        '--out_tbreak', '-OTB',
        metavar='OUTPUT_TBREAK_FILE',
        type=str,
        default='./tbreak.nc',
        help='Output file path for tbreak file'
    )

    return parser


def main(args):
    start = datetime.now()

    # ------------------------------------------------------------------------------
    # Specify model input parameters

    if not os.path.isfile(args.dem):
        raise OSError("dem argument {0} does not exist!".format(args.dem))

    if not os.path.isdir(os.path.dirname(args.out_maxus)):
        raise OSError(
            "Directory to out_maxus argument {0} does not exist!".format(
                args.out_maxus))

    inc = args.increment

    # length of outlying upwind search vector (meters)
    dmax = args.sv_global

    # length of local max upwind slope search vector (meters)
    sepdist = args.sv_local

    # Anemometer height (meters)
    inst = args.height

    # Windower
    windower = args.window

    save_file = args.out_maxus
    save_file_tb = args.out_tbreak
    # Operate on file according to file type
    dem_file = args.dem
    ext = dem_file.split('.')[-1]

    if ext == 'nc':
        data = nc.Dataset(dem_file)
        if args.var_name in data.variables:
            dem_data = data.variables[args.var_name][:]
            x = data.variables['x'][:]
            y = data.variables['y'][:]

        else:
            raise IOError(
                "{0} is not a variable provided. double check file has a "
                "variable named dem and dimensions named x and y".format(
                    args.var_name
                )
            )

    else:
        raise IOError(
            "Image must be a netcdf file (.nc)"
        )

    # ------------------------------------------------------------------------------
    # run the wind model
    # initialize the wind model with the dem
    w = wind_model(x, y, dem_data, nthreads=12)

    # calculate the maxus for the parameters and output to file
    w.maxus(dmax, inc=inc, inst=inst, out_file=save_file)
    print(datetime.now() - start)

    # window the maxus values based on the maxus values in the file
    w.windower(save_file, windower, 'maxus')

    if args.make_tbreak:
        # calculate the maxus for the parameters and output to file
        w.tbreak(dmax, sepdist, inc=inc, inst=inst, out_file=save_file_tb)

        # window the maxus values based on the maxus values in the file
        w.windower(save_file_tb, windower, 'tbreak')

    print(datetime.now() - start)


if __name__ == "__main__":
    script_arguments = argument_parser().parse_args()
    main(script_arguments)
