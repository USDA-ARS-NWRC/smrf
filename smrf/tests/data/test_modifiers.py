import unittest

import numpy as np
import pandas as pd

from smrf.data import modifiers
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
            ('input', {}, None),
            ('input', {'input_scalar_type': 'factor'}, 'input_scalar_factor'),
            ('output', {'output_scalar_type': 'factor'}, 'output_scalar_factor'),
            ('output', {}, None)
        ]
    )
    def test_get_scalar_value_key(self, stage, config, expected):
        assert modifiers.get_scalar_value_key(config, stage) == expected

    def test_get_scalar_value_key_failure(self):
        with self.assertRaises(ValueError):
            modifiers.get_scalar_value_key({}, "bad_stage")

    @parameterized.expand(
        [
            (input_array, "input_scalar_factor", {"input_scalar_factor": 2.1}, input_array * 2.1),
            (input_series, "input_scalar_factor", {"input_scalar_factor": 2.0}, pd.Series([20.4, 84.0, 10.2])),
            (input_array, "output_scalar_factor", {"output_scalar_factor": 1.0}, input_array),
            (input_array, "output_scalar_factor", {"output_scalar_factor": 1.5}, input_array * 1.5),
        ]
    )
    def test_scale_values(self, data, scalar_key, config, expected):
        result = modifiers.scale_data(data, scalar_key, config)
        if isinstance(result, np.ndarray):
            np.testing.assert_almost_equal(result, expected)
        else:
            pd.testing.assert_series_equal(result, expected)

    def test_scale_values_failure(self):
        with self.assertRaises(NotImplementedError):
            modifiers.scale_data(input_array, "bad_key", {})
