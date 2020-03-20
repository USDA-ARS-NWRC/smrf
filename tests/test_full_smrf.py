#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_full_smrf
----------------------------------

Tests for an entire smrf run. The SMRF integration run!
"""

import shutil
import unittest
from os.path import abspath, dirname, isdir, join

import numpy as np
from netCDF4 import Dataset

import smrf
from smrf.framework.model_framework import run_smrf
from tests.test_configurations import SMRFTestCase


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
    def setUpClass(self):
        """
        Runs the short simulation over reynolds mountain east
        """
        run_dir = abspath(join(dirname(smrf.__file__), '../tests', 'RME'))

        self.gold = abspath(join(run_dir, 'gold'))

        self.output = join(run_dir, 'output')

        # Remove any potential files to ensure fresh run
        if isdir(self.output):
            shutil.rmtree(self.output)

        config = join(run_dir, 'config.ini')

        run_smrf(config)

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
