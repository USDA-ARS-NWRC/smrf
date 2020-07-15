# -*- coding: utf-8 -*-
# flake8: noqa

import os

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = 'unknown'

__core_config__ = os.path.abspath(
    os.path.dirname(__file__) + '/framework/CoreConfig.ini')
__recipes__ = os.path.abspath(os.path.dirname(
    __file__) + '/framework/recipes.ini')
__config_changelog__ = os.path.abspath(
    os.path.dirname(__file__) + '/framework/changelog.ini')

__config_titles__ = {
    "topo": "Files for DEM and vegetation",
    "time": "Dates to run model",
    "stations": "Stations to use",
    "csv": "CSV section configurations",
    "gridded": "Gridded datasets configurations",
    "air_temp": "Air temperature distribution",
    "vapor_pressure": "Vapor pressure distribution",
    "wind": "Wind speed and wind direction distribution",
    "precip": "Precipitation distribution",
    "albedo": "Albedo distribution",
    "cloud_factor": "Cloud Factor - Fraction used to limit solar radiation Cloudy (0) - Sunny (1)",
    "solar": "Solar radiation",
    "thermal": "Incoming thermal radiation",
    "soil_temp": "Soil temperature",
    "output": "Output variables",
    "system": "System variables and Logging"
}

from . import utils, data, distribute, envphys, framework, output, spatial  # isort:skip

__config_header__ = "Config File for SMRF {0}\n" \
                    "For more SMRF related help see:\n" \
                    "{1}".format(
                        __version__, 'http://smrf.readthedocs.io/en/latest/')
__config_checkers__ = 'utils.utils'
# -*- coding: utf-8 -*-
