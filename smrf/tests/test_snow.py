#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_snow
----------------------------------

Tests for `envphys.snow` module.
"""

import unittest

import numpy as np

from smrf.envphys import snow


class TestNASDE(unittest.TestCase):
    def testMarks2017(self):
        """
        Tests the New Snow Density Model : marks2017
        """

        T = np.array([-10, -5, 0, 1])
        PP = np.array([100, 100, 100, 100])
        s = snow.marks2017(T, PP)
        r = [79, 115, 247, 0]

        for i, rho in enumerate(s['rho_s']):
            msg = ("NASDE Model Failed: marks2017({0},{3}) == ""{1}\nExpected "
                   "{2}".format(T[i], rho, r[i], PP[i]))
            self.assertAlmostEqual(rho, r[i], places=0, msg=msg)

    def testSusong1999(self):
        """
        Tests the New Snow Density Model : susong1999
        """

        T = np.array([-5, -3, 0])
        PP = np.array([1, 1, 1])

        s = snow.susong1999(T, PP)
        r = [100, 150, 250]
        for i, rho in enumerate(s['rho_s']):
            msg = ("NASDE Model Failed: susong1999({0},{3}) == {1}\nExpected "
                   "{2}".format(T[i], rho, r[i], PP[i]))
            self.assertAlmostEqual(rho, r[i], places=0, msg=msg)


if __name__ == '__main__':
    unittest.main()
