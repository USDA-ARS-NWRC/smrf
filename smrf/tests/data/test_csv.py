
from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import SMRF, run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestLoadCSVData(SMRFTestCase):

    def test_station_dates(self):
        """
        Test the start date not in the data
        """
        config = self.base_config

        # Use dates not in the dataset, expecting an error
        config.raw_cfg['time']['start_date'] = '1900-01-01 00:00'
        config.raw_cfg['time']['end_date'] = '1900-02-01 00:00'

        # apply the new recipes
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        with self.assertRaises(Exception):
            run_smrf(config)

    def test_all_stations(self):
        """
        Test using all stations
        """

        # test the end date
        config = self.base_config
        config.raw_cfg['csv']['stations'] = ['RMESP', 'RME_176']

        # apply the new recipies
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        self.assertIsInstance(run_smrf(config), SMRF)
