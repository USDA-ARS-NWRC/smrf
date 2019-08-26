#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, Extension
from Cython.Distutils import build_ext
import numpy
import os
import sys
from subprocess import check_output

if sys.argv[-1] != 'test':

	#Grab and write the gitVersion from 'git describe'.
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
			ls_proc = check_output(["git describe --tags"], shell=True, universal_newlines=True)
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

	with open(fname,'w') as f:
		nchars = len(gitVersion) - 1
		f.write("__gitPath__='{0}'\n".format(gitPath))
		f.write("__gitVersion__='{0}'\n".format(gitVersion[:nchars]))
		f.close()

# force the compiler to use gcc
os.environ["CC"] = "gcc"

cmdclass = {}
ext_modules = []

# detrended kriging
loc = 'smrf/spatial/dk'  # location of the dk folder
mname = os.path.join(loc, 'detrended_kriging')
mname = mname.replace('/', '.')

ext_modules += [
                Extension(mname,
                          sources=[os.path.join(loc, val) for val in [
                              "detrended_kriging.pyx",
                              "krige.c",
                              "lusolv.c",
                              "array.c"
                              ]],
                          include_dirs=[numpy.get_include()],
                          extra_compile_args=['-fopenmp', '-O3'],
                          extra_link_args=['-fopenmp', '-O3']
                          ),
                ]
cmdclass.update({'build_ext': build_ext})

# envphys core c functions
loc = 'smrf/envphys/core'  # location of the folder
mname = os.path.join(loc, 'envphys_c')
mname = mname.replace('/', '.')
ext_modules += [
                Extension(mname,
                          sources=[os.path.join(loc, val) for val in [
                              "envphys_c.pyx",
                              "topotherm.c",
                              "dewpt.c",
							  "iwbt.c"
                              ]],
                          include_dirs=[numpy.get_include()],
                          extra_compile_args=['-fopenmp', '-O3'],
                          extra_link_args=['-fopenmp', '-O3']
                          ),
                ]

# wind model c functions
loc = 'smrf/utils/wind'  # location of the folder
mname = os.path.join(loc, 'wind_c')
mname = mname.replace('/', '.')

ext_modules += [
                Extension(mname,
                          sources=[os.path.join(loc, val) for val in [
                              "wind_c.pyx",
                              "breshen.c",
                              "calc_wind.c"
                              ]],
                          include_dirs=[numpy.get_include()],
                          extra_compile_args=['-fopenmp', '-O3'],
                          extra_link_args=['-fopenmp', '-O3']
                          ),
                ]

setup(
    name='smrf',
    version='0.8.12',
    description="Distributed snow modeling for water resources",
    author="Scott Havens",
    author_email='scott.havens@ars.usda.gov',
    url='https://github.com/USDA-ARS-NWRC/smrf',
    packages=[
        'smrf',
        'smrf.data',
        'smrf.distribute',
        'smrf.envphys',
        'smrf.envphys.core',
        'smrf.framework',
        'smrf.output',
        'smrf.spatial',
        'smrf.utils',
        'smrf.utils.wind',
        'smrf.spatial.dk'
        ],
    include_package_data=True,
    package_data={'smrf':['./framework/CoreConfig.ini',
			  './framework/.qotw', './framework/recipes.ini']},
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
#     tests_require=test_requirements,
    cmdclass=cmdclass,
    ext_modules=ext_modules,
    scripts=['scripts/update_configs',
             'scripts/run_smrf',
	     'scripts/mk_project',
	     'scripts/gen_maxus']
)
