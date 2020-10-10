from smrf.envphys.snow import susong1999
import unittest
import numpy as np


class TestSusong1999(unittest.TestCase):
    def test_returns_precip(self):
        temperatures = np.random.uniform(low=-8, high=3, size=(12,12))
        precipitation = np.random.uniform(low=0.5, high=30, size=(12,12))

        results = susong1999(temperatures, precipitation)

        assert 'rho_s' in results
        assert 'pcs' in results

    def test_returns_no_precip(self):
        temperatures = np.random.uniform(low=-8, high=3, size=(12,12))
        precipitation = np.zeros((12,12))

        results = susong1999(temperatures, precipitation)

        assert 'rho_s' in results
        assert 'pcs' in results
