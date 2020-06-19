from smrf.framework.model_framework import can_i_run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestConfigurations(SMRFTestCase):

    def test_base_run(self):
        """
        Test the config for running configurations with different options
        """
        # test the base run with the config file
        result = can_i_run_smrf(self.config_file)
        self.assertTrue(result)
