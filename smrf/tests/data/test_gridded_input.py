import unittest
from unittest.mock import MagicMock

import pandas as pd

from smrf.data.gridded_input import GriddedInput
from smrf.data.load_topo import Topo


class TestDataSource(GriddedInput):
    pass


class TestGriddedInput(unittest.TestCase):
    TOPO_MOCK = MagicMock(spec=Topo, instance=True)
    BBOX = [1, 2, 3, 4]
    CONFIG_MOCK = MagicMock('config', spec_set=dict)
    START_DATE = pd.to_datetime('2021-01-01 00:00 UTC')
    END_DATE = pd.to_datetime('2021-01-02')
    VALID_ARGS = dict(
        start_date=START_DATE, end_date=END_DATE,
        topo=TOPO_MOCK, bbox=BBOX, config=CONFIG_MOCK
    )

    def test_start_date(self):
        gridded_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            self.START_DATE,
            gridded_input.start_date
        )

    def test_end_date(self):
        gridded_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            self.END_DATE,
            gridded_input.end_date
        )

    def test_time_zone(self):
        gridded_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            'UTC',
            str(gridded_input.time_zone)
        )

    def test_topo(self):
        gridded_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            self.TOPO_MOCK,
            gridded_input.topo
        )

    def test_box(self):
        gridded_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            self.BBOX,
            gridded_input.bbox
        )

    def test_config(self):
        config_values = MagicMock('Gridded Config')
        smrf_config = {GriddedInput.TYPE: config_values}
        self.CONFIG_MOCK.__getitem__.side_effect = smrf_config.__getitem__

        gridded_input = GriddedInput(**self.VALID_ARGS)

        self.assertEqual(
            config_values,
            gridded_input.config
        )

    def test_invalid_start_date_argument(self):
        with self.assertRaisesRegex(TypeError, 'Argument start_date'):
            GriddedInput(
                '2021-01-01', self.END_DATE,
                bbox=self.BBOX, config={}, topo=self.TOPO_MOCK
            )

    def test_invalid_topo_argument(self):
        with self.assertRaisesRegex(TypeError, 'Argument topo'):
            GriddedInput(
                self.START_DATE, self.END_DATE,
                bbox=self.BBOX, config={}, topo=object
            )

    def test_invalid_bbox_argument(self):
        with self.assertRaisesRegex(TypeError, 'Argument bbox'):
            GriddedInput(
                self.START_DATE, self.END_DATE,
                topo=self.TOPO_MOCK, config={}, bbox=[]
            )

    def test_logger_name(self):
        data_source = TestDataSource(**self.VALID_ARGS)

        self.assertEqual(
            data_source.__class__.__name__,
            data_source._logger.name
        )
