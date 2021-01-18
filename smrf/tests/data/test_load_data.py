from contextlib import contextmanager

import mock

import smrf.data as smrf_data
from smrf.tests.smrf_test_case import SMRFTestCase
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


@contextmanager
def mock_for_data_load():
    with mock.patch.multiple(
        smrf_data.InputData,
        set_variables=mock.DEFAULT,
        metadata_pixel_location=mock.DEFAULT
    ):
        yield


class TestLoadData(SMRFTestCase):
    def setUp(self):
        super(TestLoadData, self).setUp()
        self.smrf = self.smrf_instance
        self.smrf.loadTopo()

    @mock.patch.object(smrf_data.InputCSV, 'check_colocation')
    @mock.patch.object(smrf_data.InputCSV, 'load')
    def test_csv_type(self, mock_check_colocation, mock_load):
        with mock_for_data_load():
            load_data = smrf_data.InputData(
                self.smrf.config,
                self.smrf.start_date,
                self.smrf.end_date,
                self.smrf.topo,
            )

        self.assertEqual(
            smrf_data.InputCSV.DATA_TYPE,
            load_data.data_type
        )
        mock_load.assert_called()
        mock_check_colocation.assert_called()

    def test_missing_data_type(self):
        del self.smrf.config['csv']

        with mock_for_data_load():
            with self.assertRaisesRegex(AttributeError, 'Missing required'):
                smrf_data.InputData(
                    self.smrf.config,
                    self.smrf.start_date,
                    self.smrf.end_date,
                    self.smrf.topo,
                )


class TestInputDataGridded(SMRFTestCaseLakes):
    @mock.patch.object(smrf_data.InputGribHRRR, 'load')
    def test_data_type(self, mock_load):
        self.smrf = self.smrf_instance
        self.smrf.loadTopo()

        with mock_for_data_load():
            load_data = smrf_data.InputData(
                self.smrf.config,
                self.smrf.start_date,
                self.smrf.end_date,
                self.smrf.topo,
            )

        self.assertEqual(
            smrf_data.InputGribHRRR.DATA_TYPE,
            load_data.data_type
        )
        mock_load.assert_called()
