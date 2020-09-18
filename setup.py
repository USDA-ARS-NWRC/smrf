#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext as _build_ext

# Test if compiling with cython or using the C source
try:
    from Cython.Distutils import build_ext as _build_ext
except ImportError:
    USE_CYTHON = False
else:
    USE_CYTHON = True

print('Using Cython {}'.format(USE_CYTHON))
ext = '.pyx' if USE_CYTHON else '.c'


def c_name_from_path(location, name):
    return os.path.join(location, name).replace('/', '.')


class build_ext(_build_ext):
    def finalize_options(self):
        _build_ext.finalize_options(self)
        # Prevent numpy from thinking it is still in its setup process:
        __builtins__.__NUMPY_SETUP__ = False
        import numpy
        self.include_dirs.append(numpy.get_include())


# Give user option to specify his local compiler name
if "CC" not in os.environ:
    os.environ["CC"] = "gcc"

ext_modules = []
extension_params = dict(
    extra_compile_args=['-fopenmp', '-O3'],
    extra_link_args=['-fopenmp', '-O3'],
)

# detrended kriging
source_folder = 'smrf/spatial/dk'
ext_modules += [
    Extension(
        c_name_from_path(source_folder, 'detrended_kriging'),
        sources=[os.path.join(source_folder, val) for val in [
            "detrended_kriging" + ext,
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
            "envphys_c" + ext,
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
            "wind_c" + ext,
            "breshen.c",
            "calc_wind.c"
        ]],
        **extension_params
    ),
]

cmdclass = {}
if USE_CYTHON:
    cmdclass = {'build_ext': build_ext}

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read()

with open('README.md') as readme_file:
    readme = readme_file.read()

setup(
    name='smrf-dev',
    description="Distributed snow modeling for water resources",
    author="Scott Havens",
    author_email='scott.havens@ars.usda.gov',
    url='https://github.com/USDA-ARS-NWRC/smrf',
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=find_packages(include=['smrf', 'smrf.*']),
    install_requires=requirements,
    python_requires='>3.5',
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
        'Natural Language :: English',
        'License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    test_suite='smrf.tests',
    # tests_require=test_requirements,
    cmdclass=cmdclass,
    ext_modules=ext_modules,
    scripts=[
        'scripts/update_configs',
        'scripts/run_smrf',
        'scripts/gen_maxus'
    ],
    extras_require={
        'docs': [
            'sphinxcontrib-bibtex',
            'sphinxcontrib-websupport',
            'pydata-sphinx-theme'
        ]
    },
    use_scm_version={
        'local_scheme': 'node-and-date',
    },
    setup_requires=[
        'setuptools_scm',
        'numpy'
    ],
)
