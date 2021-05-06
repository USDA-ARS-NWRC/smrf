import unittest
from unittest.mock import MagicMock

import pandas as pd

from smrf.data.hrrr_grib import InputGribHRRR
from smrf.data.load_topo import Topo
from smrf.distribute.wind.wind_ninja import WindNinjaModel


class TestInputGribHRRR(unittest.TestCase):
    TOPO_MOCK = MagicMock(spec=Topo, instance=True)
    BBOX = [1, 2, 3, 4]
    START_DATE = pd.to_datetime('2021-01-01 00:00 UTC')
    END_DATE = pd.to_datetime('2021-01-02')
    SMRF_CONFIG = {
        'gridded': {
            'hrrr_load_method': 'timestep',
        }
    }

    def test_load_method_config(self):
        hrrr_input = InputGribHRRR(
            self.START_DATE, self.END_DATE,
            topo=self.TOPO_MOCK, bbox=self.BBOX,
            config=self.SMRF_CONFIG,
        )

        self.assertEqual(
            self.START_DATE,
            hrrr_input.start_date
        )
        self.assertEqual(
            self.START_DATE + pd.to_timedelta(20, 'minutes'),
            hrrr_input.end_date
        )
        self.assertEqual(
            None,
            hrrr_input.cf_memory
        )

    def test_load_wind(self):
        hrrr_input = InputGribHRRR(
            self.START_DATE, self.END_DATE,
            topo=self.TOPO_MOCK, bbox=self.BBOX,
            config={
                **self.SMRF_CONFIG,
                'wind': {'wind_model': 'other'}
            }
        )

        self.assertTrue(hrrr_input._load_wind)
        self.assertTrue('wind_speed' in hrrr_input.variables)
        self.assertTrue('wind_direction' in hrrr_input.variables)

    def test_skip_load_wind(self):
        hrrr_input = InputGribHRRR(
            self.START_DATE, self.END_DATE,
            topo=self.TOPO_MOCK, bbox=self.BBOX,
            config={
                **self.SMRF_CONFIG,
                'wind': {'wind_model': WindNinjaModel.MODEL_TYPE}
            }
        )

        self.assertFalse(hrrr_input._load_wind)
        self.assertCountEqual(
            InputGribHRRR.VARIABLES,
            hrrr_input.variables
        )
