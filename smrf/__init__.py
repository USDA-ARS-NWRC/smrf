# -*- coding: utf-8 -*-
'''
SMRF - Snow Modeling Resource Framework
'''
__author__ = 'Scott Havens'
__email__ = 'scotthavens@ars.usda.gov'
__version__ = '0.2.5'
__gitHash__='4eb2eb0'
import os
__core_config__ = os.path.abspath(os.path.dirname(__file__)+'/framework/CoreConfig.ini')
from . import data
from . import distribute
from . import envphys
from . import ipw
from . import framework
from . import spatial
from . import utils
from . import model
from . import output
# -*- coding: utf-8 -*-
