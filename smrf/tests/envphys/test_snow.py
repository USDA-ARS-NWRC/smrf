from smrf.envphys import Snow
from smrf.envphys.nasde_model import Marks2017, PiecewiseSusong1999, Susong1999
import mock
import unittest
import numpy as np


class TestSnow(unittest.TestCase):
    TEMPERATURES = np.random.uniform(low=-8, high=3, size=(12, 12))
    PRECIPITATION = np.random.uniform(low=0, high=3, size=TEMPERATURES.shape)

    def test_missing_model(self):
        with self.assertRaises(ValueError):
            Snow.phase_and_density(self.TEMPERATURES, self.PRECIPITATION, '')

    @mock.patch.object(Susong1999, 'run')
    def test_passes_arguments(self, model_patch):
        Snow.phase_and_density(
            self.TEMPERATURES, self.PRECIPITATION, 'susong1999'
        )
        call_args = model_patch.call_args
        np.testing.assert_equal(self.TEMPERATURES, call_args[0][0])
        np.testing.assert_equal(self.PRECIPITATION, call_args[0][1])

    @mock.patch.object(Susong1999, 'run')
    def test_susong_1999(self, model_patch):
        Snow.phase_and_density(
            self.TEMPERATURES, self.PRECIPITATION, 'susong1999'
        )
        model_patch.assert_called()

    @mock.patch.object(PiecewiseSusong1999, 'run')
    def test_piecewise_susong_1999(self, model_patch):
        Snow.phase_and_density(
            self.TEMPERATURES, self.PRECIPITATION, 'piecewise_susong1999'
        )
        model_patch.assert_called()

    @mock.patch.object(Marks2017, 'run')
    def test_marks_2017(self, model_patch):
        Snow.phase_and_density(
            self.TEMPERATURES, self.PRECIPITATION, 'marks2017'
        )
        model_patch.assert_called()
