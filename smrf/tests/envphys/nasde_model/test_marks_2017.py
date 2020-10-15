from smrf.envphys.nasde_model import Marks2017
import unittest
import numpy as np


class TestMarks2017(unittest.TestCase):
    TEMPERATURES = np.array([-10, -5, 0, 1])
    PRECIPITATION = np.array([100, 100, 100, 100])

    def test_returns_precipitation(self):
        results = Marks2017.run(self.TEMPERATURES, self.PRECIPITATION)

        np.testing.assert_almost_equal(
            results['rho_s'], [79, 115, 247, 0], decimal=0
        )
        assert 'pcs' in results
