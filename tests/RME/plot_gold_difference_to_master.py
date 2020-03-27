#
# Script to plot difference in gold files between current branch and master
#

import os
from glob import glob
from pathlib import PurePath

import matplotlib.pyplot as plt
import netCDF4
import numpy
import pygit2

import smrf

SMRF_FOLDER = os.path.abspath(os.path.dirname(smrf.__file__) + '/..')
GOLD_FOLDERS = ['gold', 'gold_hrrr']

SMRF_REPO = pygit2.Repository(SMRF_FOLDER)
CURRENT_BRANCH = SMRF_REPO.head.name
MASTER_BRANCH = SMRF_REPO.branches['master']

LABEL = "Min: {:.3E}\nMax: {:.3E}\nMean: {:.3E}"


def get_file_values(branch, file):
    SMRF_REPO.checkout(branch)
    print(f"Getting data from {SMRF_REPO.head.name} for {file}")

    branch_data = netCDF4.Dataset(file)
    variable_data = [
        branch_data[variable][:] for variable
        in branch_data.variables.keys()
        if variable not in ['x', 'y', 'time', 'projection']
    ]
    branch_data.close()
    return variable_data[0].flatten()


def plot_difference():
    for folder in GOLD_FOLDERS:
        gold_dir = os.path.abspath(
            os.path.join(SMRF_FOLDER, 'tests', 'RME', folder)
        )

        for gold_file in glob(gold_dir + '/*.nc'):
            branch_data = get_file_values(CURRENT_BRANCH, gold_file)
            master_data = get_file_values(MASTER_BRANCH, gold_file)
            file_name = PurePath(gold_file).name

            difference = branch_data - master_data
            plt.figure()
            plt.xlim(-.01, .01)
            plt.hist(
                difference,
                label=LABEL.format(
                    difference.min(),
                    difference.max(),
                    difference.mean()
                ),
                bins=numpy.arange(-.5, .5, .001),
            )
            plt.title(f"{folder.replace('_', ' ').upper()}\n {file_name}")
            plt.legend()
            plt.savefig(f"{folder}_hist_{file_name}.png")


if __name__ == '__main__':
    SMRF_REPO.checkout(CURRENT_BRANCH)
    plot_difference()
    SMRF_REPO.checkout(CURRENT_BRANCH)
