import unittest

import mock

from smrf.distribute.wind import Wind
from smrf.distribute.wind.wind_ninja import WindNinjaModel
from smrf.distribute.wind.winstral import WinstralWindModel


class TestWind(unittest.TestCase):
    CONFIG = {
        'wind': {
            'wind_model': None
        }
    }

    def test_interp_init(self):
        self.CONFIG['wind']['wind_model'] = Wind.INTERP
        wind_instance = Wind(self.CONFIG)

        self.assertTrue(
            Wind.INTERP,
            wind_instance.wind_model
        )
        self.assertTrue(
            wind_instance.model_type(Wind.INTERP)
        )

    @mock.patch.object(WindNinjaModel, '__init__', return_value=None)
    def test_wind_ninja_init(self, mock_model):
        self.CONFIG['wind']['wind_model'] = WindNinjaModel.MODEL_TYPE
        wind_instance = Wind(self.CONFIG)

        self.assertTrue(mock_model.called)
        self.assertIsInstance(
            wind_instance.wind_model,
            WindNinjaModel
        )
        self.assertTrue(
            wind_instance.model_type(WindNinjaModel.MODEL_TYPE)
        )

    @mock.patch.object(WinstralWindModel, '__init__', return_value=None)
    def test_winstral_init(self, mock_model):
        self.CONFIG['wind']['wind_model'] = WinstralWindModel.MODEL_TYPE
        wind_instance = Wind(self.CONFIG)

        self.assertTrue(mock_model.called)
        self.assertIsInstance(
            wind_instance.wind_model,
            WinstralWindModel
        )
        self.assertTrue(
            wind_instance.model_type(WinstralWindModel.MODEL_TYPE)
        )

    def test_config_model_type_true(self):
        self.assertTrue(
            Wind.config_model_type(
                {'wind': {'wind_model': 'model'}}, 'model'
            )
        )

    def test_config_model_type_false(self):
        self.assertFalse(
            Wind.config_model_type(
                {}, 'model'
            )
        )
        self.assertFalse(
            Wind.config_model_type(
                {'wind': {'parameter': 1}}, 'model'
            )
        )
