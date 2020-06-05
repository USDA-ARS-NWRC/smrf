#
# Script to plot difference in gold files between current branch and master
# Must be ran from the project root directory
#

import os
from goldmeister.compare import GoldGitBranchCompare

files = [
    'air_temp',
    'net_solar',
    'percent_snow',
    'precip_temp',
    'precip',
    'snow_density',
    'thermal',
    'vapor_pressure',
    'wind_direction',
    'wind_speed'
]


def main():

    repo_path = os.getcwd()

    gold_files = [
        os.path.join(repo_path, 'tests', 'RME', 'gold', f"{gf}.nc") for gf in files
    ]

    gc = GoldGitBranchCompare(
        repo_path=repo_path,
        gold_files=gold_files,
        file_type='netcdf',
        old_branch='upstream/master',
        new_branch='origin/156_topocalc')

    results = gc.compare()

    gc.plot_results(results, plot_original_data=True, include_hist=True)


if __name__ == '__main__':
    main()
    # SMRF_REPO.checkout(CURRENT_BRANCH)
    # plot_difference()
    # SMRF_REPO.checkout(CURRENT_BRANCH)
