# -*- coding: utf-8 -*-
'''
SMRF - Snow Modeling Resource Framework
'''
__version__ = '0.8.12'

import os

__core_config__ = os.path.abspath(os.path.dirname(__file__)+'/framework/CoreConfig.ini')
__recipes__ = os.path.abspath(os.path.dirname(__file__)+'/framework/recipes.ini')

from . import data
from . import distribute
from . import envphys
from . import framework
from . import spatial
from . import utils
from . import output

__config_titles__ = {
                "topo":"Files for DEM and vegetation",
                "time": "Dates to run model",
                "stations":"Stations to use",
                "csv":"CSV section configurations",
                "mysql":"MySQL database",
                "air_temp":"Air temperature distribution",
                "vapor_pressure":"Vapor pressure distribution",
                "wind": "Wind speed and wind direction distribution",
                "precip": "Precipitation distribution",
                "albedo":"Albedo distribution",
                "solar":"Solar radiation distribution",
                "thermal":"Thermal radiation distribution",
                "soil_temp":"Soil temperature",
                "output":"Output variables",
                "logging":"Logging",
                "system":"System variables"
}

__config_header__ = utils.utils.getConfigHeader()
__config_checkers__ = 'utils.utils'
# -*- coding: utf-8 -*-
