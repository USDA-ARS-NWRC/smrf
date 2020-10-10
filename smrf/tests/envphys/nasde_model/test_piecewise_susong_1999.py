from smrf.envphys.nasde_model import PiecewiseSusong1999
import unittest
import numpy as np


class TestPiecewiseSusong1999(unittest.TestCase):
    TEMPERATURES = np.random.uniform(low=0, high=3, size=12)
    PRECIPITATION = np.random.uniform(
        low=0.5, high=30, size=TEMPERATURES.size
    )

    def test_returns_precipitation(self):
        results = PiecewiseSusong1999.run(
            self.TEMPERATURES, self.PRECIPITATION
        )

        assert 'rho_s' in results
        assert 'pcs' in results
