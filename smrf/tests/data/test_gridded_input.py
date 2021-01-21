import unittest

import pandas as pd

from smrf.data.gridded_input import GriddedInput


class TestDataSource(GriddedInput):
    pass


class TestGriddedInput(unittest.TestCase):
    START_DATE = pd.to_datetime('2021-01-01 00:00 UTC')
    END_DATE = pd.to_datetime('2021-01-02')
    VALID_ARGS = dict(
        start_date=START_DATE, end_date=END_DATE,
        topo=object, bbox=[], config={}
    )

    def test_start_date(self):
        hrrr_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            self.START_DATE,
            hrrr_input.start_date
        )

    def test_end_date(self):
        hrrr_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            self.END_DATE,
            hrrr_input.end_date
        )

    def test_time_zone(self):
        hrrr_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            'UTC',
            str(hrrr_input.time_zone)
        )

    def test_missing_topo_argument(self):
        with self.assertRaisesRegex(TypeError, 'Missing argument: topo'):
            GriddedInput(
                self.START_DATE, self.END_DATE,
                bbox=[], config={}
            )

    def test_missing_bbox_argument(self):
        with self.assertRaisesRegex(TypeError, 'Missing argument: bbox'):
            GriddedInput(
                self.START_DATE, self.END_DATE,
                topo=object, config={}
            )

    def test_missing_config_argument(self):
        with self.assertRaisesRegex(TypeError, 'Missing argument: config'):
            GriddedInput(
                self.START_DATE, self.END_DATE,
                topo=object, bbox=[]
            )

    def test_logger_name(self):
        data_source = TestDataSource(**self.VALID_ARGS)

        self.assertEqual(
            data_source.__class__.__name__,
            data_source._logger.name
        )
