from smrf.envphys.nasde_model import Susong1999
import unittest
import numpy as np


class TestSusong1999(unittest.TestCase):
    TEMPERATURES = np.array([-5, -3, 0])
    PRECIPITATION = np.array([1, 1, 1])

    def test_returns_precipitation(self):
        results = Susong1999.run(self.TEMPERATURES, self.PRECIPITATION)

        np.testing.assert_equal(results['rho_s'], [100, 150, 250])
        assert 'pcs' in results

    def test_returns_no_precipitation(self):
        precipitation = np.zeros(self.TEMPERATURES.shape)

        results = Susong1999.run(self.TEMPERATURES, precipitation)

        assert 'rho_s' in results
        assert 'pcs' in results
