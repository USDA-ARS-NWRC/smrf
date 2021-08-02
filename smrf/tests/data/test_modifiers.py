import unittest

import numpy as np
import pandas as pd

from smrf.data.modifiers import Modifiers
from parameterized import parameterized


input_array = np.array([
    [1.0, 1.1, 1.2],
    [3.1, 3.2, 5.7],
    [0.1, -1.1, 2.0]
])

input_series = pd.Series([10.2, 42.0, 5.1])


class TestModifiers(unittest.TestCase):
    @parameterized.expand(
        [
            ({}, None, None, None),
            (
                {'input_scalar_type': 'factor', 'input_scalar_factor': 2.0},
                2.0, None, None),
            (
                {'output_scalar_type': 'factor', 'output_scalar_factor': 1.2},
                None, 1.2, None),
            ({}, None, None, None),
            (
                {'input_scalar_type': 'factor', 'input_scalar_factor': 2.0,
                 'output_scalar_type': 'factor', 'output_scalar_factor': 1.2},
                2.0, 1.2, None),
            ({'input_scalar_type': 'foo'}, None, None, ValueError)
        ]
    )
    def test_get_scalar(self, config, expected_input_scalar,
                        expected_output_scalar, expected_exception):
        if expected_exception is not None:
            with self.assertRaises(expected_exception):
                Modifiers.from_variable_config(config)
        else:
            mod = Modifiers.from_variable_config(config)
            self.assertEqual(mod._input_scalar, expected_input_scalar)
            self.assertEqual(mod._output_scalar, expected_output_scalar)

    @parameterized.expand(
        [
            (input_array, Modifiers(2.1, None), input_array * 2.1),
            (input_series, Modifiers(2.0, None),
             pd.Series([20.4, 84.0, 10.2])),
            (input_array, Modifiers(None, None), input_array)
        ]
    )
    def test_scale_input_data(self, data, mod, expected):
        result = mod.scale_input_data(data)
        if isinstance(result, np.ndarray):
            np.testing.assert_almost_equal(result, expected)
        else:
            pd.testing.assert_series_equal(result, expected)

    @parameterized.expand(
        [
            (input_array, Modifiers(None, 1.0), input_array),
            (input_array, Modifiers(None, 1.5), input_array * 1.5),
            (input_array, Modifiers(None, None), input_array)
        ]
    )
    def test_scale_output_data(self, data, mod, expected):
        result = mod.scale_output_data(data)
        if isinstance(result, np.ndarray):
            np.testing.assert_almost_equal(result, expected)
        else:
            pd.testing.assert_series_equal(result, expected)
