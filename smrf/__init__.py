# -*- coding: utf-8 -*-
'''
SMRF - Snow Modeling Resource Framework
'''
__version__ = '0.4.2'
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
