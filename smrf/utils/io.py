#!/usr/bin/env python
"""
Input/Output functions
Adapted from the UW-Hydro tonic project
"""
from __future__ import print_function

import os
import sys
from collections import Sequence
from datetime import date

import pandas as pd
import pytz

from smrf import __core_config__, __version__

from .pycompat import OrderedDict, SafeConfigParser, basestring, unicode_type

# hack for install with either version 2 or version 3 python
if sys.version_info[0] >= 3:
    from smrf.utils import utils
else:
    import utils



def isbool(x):
    '''Test if str is an bolean'''
    if isinstance(x, float) or isinstance(x, basestring) and '.' in x:
        return False
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def isfloat(x):
    '''Test if value is a float'''
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def isint(x):
    '''Test if value is an integer'''
    if isinstance(x, float) or isinstance(x, basestring) and '.' in x:
        return False
    try:
        a = float(x)
        b = int(a)
    except ValueError:
        return False
    else:
        return a == b


def isscalar(x):
    '''Test if a value is a scalar'''
    if isinstance(x, (Sequence, basestring, unicode_type)):
        return False
    else:
        return True
