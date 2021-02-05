import unittest
from unittest.mock import MagicMock

import pandas as pd

import smrf.data as smrf_data
from smrf.data.load_topo import Topo


class TestInputGribHRRR(unittest.TestCase):
    TOPO_MOCK = MagicMock(spec=Topo, instance=True)
    BBOX = [1, 2, 3, 4]
    START_DATE = pd.to_datetime('2021-01-01 00:00 UTC')
    END_DATE = pd.to_datetime('2021-01-02')

    def test_load_method_config(self):
        hrrr_input = smrf_data.InputGribHRRR(
            self.START_DATE, self.END_DATE,
            topo=self.TOPO_MOCK, bbox=self.BBOX,
            config={'hrrr_load_method': 'timestep'}
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
