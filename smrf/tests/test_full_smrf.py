from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase
from smrf.tests.check_mixin import CheckSMRFOutputs


class TestThreadedRME(CheckSMRFOutputs, SMRFTestCase):
    """
    Integration test for SMRF.
    Runs the short simulation over reynolds mountain east.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.gold_dir = cls.basin_dir.joinpath('gold')

        run_smrf(cls.run_config)


class TestRME(TestThreadedRME):
    """
    Integration test for SMRF using without threading
    Runs the short simulation over reynolds mountain east
    """

    @classmethod
    def configure(cls):

        config = cls.base_config_copy()
        config.raw_cfg['system']['threading'] = False

        config.apply_recipes()
        cls.run_config = cast_all_variables(config, config.mcfg)
