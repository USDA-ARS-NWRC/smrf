#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from subprocess import check_output

import numpy
from Cython.Distutils import build_ext
from setuptools import Extension, setup, find_packages

if sys.argv[-1] != 'test':

    # Grab and write the gitVersion from 'git describe'.
    gitVersion = ''
    gitPath = ''

    # get git describe if in git repository
    print('Fetching most recent git tags')
    if os.path.exists('./.git'):
        try:
            # if we are in a git repo, fetch most recent tags
            check_output(["git fetch --tags"], shell=True)
        except Exception as e:
            print('Unable to fetch most recent tags')

        try:
            ls_proc = check_output(["git describe --tags"], shell=True,
                                   universal_newlines=True)
            gitVersion = ls_proc
            print('Checking most recent version')
        except Exception as e:
            print('Unable to get git tag and hash')
    # if not in git repo
    else:
        print('Not in git repository')
        gitVersion = ''

    # get current working directory to define git path
    gitPath = os.getcwd()

    # git untracked file to store version and path
    fname = os.path.abspath(os.path.expanduser('./smrf/utils/gitinfo.py'))

    with open(fname, 'w') as f:
        nchars = len(gitVersion) - 1
        f.write("__gitPath__='{0}'\n".format(gitPath))
        f.write("__gitVersion__='{0}'\n".format(gitVersion[:nchars]))
        f.close()


def c_name_from_path(location, name):
    return os.path.join(location, name).replace('/', '.')


# Give user option to specify his local compiler name
if "CC" not in os.environ:
    # force the compiler to use gcc
    os.environ["CC"] = "gcc"


ext_modules = []
extension_params = dict(
    include_dirs=[numpy.get_include()],
    extra_compile_args=['-fopenmp', '-O3'],
    extra_link_args=['-fopenmp', '-O3'],
)

# detrended kriging
source_folder = 'smrf/spatial/dk'
ext_modules += [
    Extension(
        c_name_from_path(source_folder, 'detrended_kriging'),
        sources=[os.path.join(source_folder, val) for val in [
            "detrended_kriging.pyx",
            "krige.c",
            "lusolv.c",
            "array.c"
        ]],
        **extension_params
    ),
]

# envphys core c functions
source_folder = 'smrf/envphys/core'
ext_modules += [
    Extension(
        c_name_from_path(source_folder, 'envphys_c'),
        sources=[os.path.join(source_folder, val) for val in [
            "envphys_c.pyx",
            "topotherm.c",
            "dewpt.c",
            "iwbt.c"
        ]],
        **extension_params
    ),
]

# wind model c functions
source_folder = 'smrf/utils/wind'
ext_modules += [
    Extension(
        c_name_from_path(source_folder, 'wind_c'),
        sources=[os.path.join(source_folder, val) for val in [
            "wind_c.pyx",
            "breshen.c",
            "calc_wind.c"
        ]],
        **extension_params
    ),
]

setup(
    name='smrf',
    version='0.9.1',
    description="Distributed snow modeling for water resources",
    author="Scott Havens",
    author_email='scott.havens@ars.usda.gov',
    url='https://github.com/USDA-ARS-NWRC/smrf',
    packages=find_packages(include=['smrf', 'smrf.*']),
    include_package_data=True,
    package_data={
        'smrf': [
            './framework/CoreConfig.ini',
            './framework/.qotw',
            './framework/recipes.ini',
            './framework/changelog.ini'
        ]
    },
    license="CC0 1.0",
    zip_safe=False,
    keywords='smrf',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: CC0 1.0',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    # tests_require=test_requirements,
    cmdclass={
        'build_ext': build_ext
    },
    ext_modules=ext_modules,
    scripts=[
        'scripts/update_configs',
        'scripts/run_smrf',
        'scripts/mk_project',
        'scripts/gen_maxus'
    ]
)
