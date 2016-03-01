#!/usr/bin/env python
# -*- coding: utf-8 -*-


#try:
#    from setuptools import setup
#except ImportError:
#    from distutils.core import setup


from distutils.core import setup
from distutils.extension import Extension
#from setuptools import setup, Extension, find_packages
#from setuptools import find_packages

#try:
#    from Cython.Distutils import build_ext
#except ImportError:
#    from distutils.command import build_ext

import numpy
import os

# force the compiler to use gcc    
os.environ["CC"] = "gcc"

#print find_packages()

#try:
from Cython.Distutils import build_ext
#except ImportError:
#    use_cython = False
#else:
#    use_cython = True

cmdclass = { }
ext_modules = [ ]

loc = 'smrf/spatial/dk' # location of the dk folder
mname = os.path.join(loc, 'detrended_kriging')
mname = mname.replace('/', '.')

#if use_cython:
ext_modules += [
                Extension(mname,
                          sources=[os.path.join(loc, val) for val in ["detrended_kriging.pyx", "krige.c", "lusolv.c", "array.c"]],
                          include_dirs=[numpy.get_include()],
                          extra_compile_args=['-fopenmp'],
                          extra_link_args=['-fopenmp']
                          ),
                ]
cmdclass.update({ 'build_ext': build_ext })
#else:
#    ext_modules += [
#                    Extension(mname,
#                              sources=[os.path.join(loc, val) for val in ["detrended_kriging.c", "krige.c", "lusolv.c", "array.c"]],
#                              include_dirs=[numpy.get_include()],
#                              extra_compile_args=['-fopenmp'],
#                              extra_link_args=['-fopenmp']
#                              )
#                    ]




with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Cython >= 0.23.4',
    'pytz >= 2013.7',
    'setuptools >= 19.6',
    'utm >= 0.4.0',
#     'cryptography >= 1.2.2',
    'mysql_connector_repackaged >= 0.3.1',
    'netCDF4 >= 1.2.1',
    'numpy >= 1.10.4',
    'pandas >= 0.17.1',
    'scipy >= 0.16.0'
]

test_requirements = [
    # TODO: put package test requirements here
]



setup(
    name='smrf',
    version='0.1.0',
    description="Distributed snow modeling for water resources",
    long_description=readme + '\n\n' + history,
    author="Scott Havens",
    author_email='scotthavens@ars.usda.gov',
    url='https://gitlab.com/ars-snow/smrf',
    packages=['smrf', 'smrf.data', 'smrf.distribute', 'smrf.envphys', 'smrf.framework', 'smrf.ipw', 'smrf.model', 'smrf.output', 'smrf.spatial', 'smrf.utils', 'smrf.spatial.dk'],
#     package_dir={'smrf':'smrf'},
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='smrf',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    cmdclass = cmdclass,
    ext_modules = ext_modules,
)
