#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_full_smrf
----------------------------------

Tests for an entire smrf run. The SMRF integration run!
"""

import shutil
import unittest
from os.path import abspath, isdir, join

import numpy as np
from netCDF4 import Dataset

from smrf.framework.model_framework import run_smrf
from tests.smrf_test_case import SMRFTestCase


def compare_image(v_name, gold_dir, test_dir):
    """
    Compares two netcdfs images to and determines if they are the same.

    Args:
        v_name: Name with in the file contains
        gold_dir: Directory containing gold standard results
        test_dir: Directory containing test results to be compared

    Returns:
        Boolean: Whether the two images were the same
    """

    image1 = join(gold_dir, v_name + '.nc')
    image2 = join(test_dir, v_name + '.nc')
    d1 = Dataset(image1, 'r')
    gold = d1.variables[v_name][:]
    d1.close()

    d2 = Dataset(image2, 'r')
    rough = d2.variables[v_name][:]
    d2.close()

    result = np.abs(gold - rough)
    return not np.any(result > 0)


class TestRME(SMRFTestCase):
    """
    Integration test for SMRF using reynolds mountain east
    """
    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """
        super().setUpClass()

        cls.gold = abspath(join(cls.test_dir, 'RME', 'gold'))
        cls.output = join(cls.test_dir, 'RME', 'output')

        # Remove any potential files to ensure fresh run
        if isdir(cls.output):
            shutil.rmtree(cls.output)

        run_smrf(cls.config_file)

    def test_variables(self):
        """
        Compare that the entire output datasets to confirm they are the same as
        the gold file provided.
        """
        variables = ['air_temp', 'precip_temp', 'net_solar',
                     'percent_snow', 'precip', 'thermal', 'wind_speed',
                     'wind_direction', 'snow_density', 'vapor_pressure']

        for v in variables:
            self.assertTrue(compare_image(v, self.gold, self.output))


if __name__ == '__main__':
    unittest.main()
