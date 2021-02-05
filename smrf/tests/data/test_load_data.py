import mock

import smrf.data as smrf_data
from smrf.tests.smrf_test_case import SMRFTestCase
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


def mock_for_data_load(test_case):
    with mock.patch.multiple(
        smrf_data.InputData,
        set_variables=mock.DEFAULT,
        metadata_pixel_location=mock.DEFAULT
    ):
        input_data = smrf_data.InputData(
            test_case.smrf.config,
            test_case.smrf.start_date,
            test_case.smrf.end_date,
            test_case.smrf.topo,
        )
    return input_data


class TestLoadData(SMRFTestCase):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.smrf = self.smrf_instance
        self.smrf.loadTopo()

    @mock.patch.object(smrf_data.InputCSV, 'check_colocation')
    @mock.patch.object(smrf_data.InputCSV, 'load')
    def test_csv_type(self, mock_check_colocation, mock_load):
        load_data = mock_for_data_load(self)

        self.assertEqual(
            smrf_data.InputCSV.DATA_TYPE,
            load_data.data_type
        )
        self.assertEqual(
            self.smrf.start_date,
            load_data.start_date
        )
        self.assertEqual(
            self.smrf.end_date,
            load_data.end_date
        )

        mock_load.assert_called()
        mock_check_colocation.assert_called()

    def test_missing_data_type(self):
        del self.smrf.config['csv']
        with self.assertRaisesRegex(AttributeError, 'Missing required'):
            mock_for_data_load(self)


class TestInputDataGridded(SMRFTestCaseLakes):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.smrf = self.smrf_instance
        self.smrf.loadTopo()

    def assert_parameters(self, instance):
        for parameter in ['start_date', 'end_date', 'topo']:
            self.assertEqual(
                getattr(self.smrf, parameter),
                getattr(instance, parameter)
            )

    @mock.patch.object(smrf_data.InputGribHRRR, 'load')
    def test_data_type(self, mock_load):
        load_data = mock_for_data_load(self)

        self.assertEqual(
            smrf_data.InputGribHRRR.DATA_TYPE,
            load_data.data_type
        )
        self.assert_parameters(load_data)

        mock_load.assert_called()

    @mock.patch.object(smrf_data.InputNetcdf, 'load')
    def test_netcdf_type(self, mock_load):
        self.smrf.config['gridded']['data_type'] = 'netcdf'
        self.smrf.config['gridded']['netcdf_file'] = {}
        load_data = mock_for_data_load(self)

        self.assertEqual(
            smrf_data.InputNetcdf.DATA_TYPE,
            load_data.data_type
        )
        self.assert_parameters(load_data)

        mock_load.assert_called()

    @mock.patch.object(smrf_data.InputWRF, 'load')
    def test_wrf_type(self, mock_load):
        self.smrf.config['gridded']['data_type'] = 'wrf'
        load_data = mock_for_data_load(self)

        self.assertEqual(
            smrf_data.InputWRF.DATA_TYPE,
            load_data.data_type
        )
        self.assert_parameters(load_data)

        mock_load.assert_called()

    def test_unknown_data_type(self):
        self.smrf.config['gridded']['data_type'] = 'unknown'
        with self.assertRaisesRegex(AttributeError, 'Unknown gridded'):
            mock_for_data_load(self)
