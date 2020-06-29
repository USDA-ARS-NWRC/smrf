#!/usr/bin/env python
"""
Input/Output functions
Adapted from the UW-Hydro tonic project
"""

from collections import Sequence

from .pycompat import basestring, unicode_type


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
