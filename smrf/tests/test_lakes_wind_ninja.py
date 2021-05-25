from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes
from smrf.tests.check_mixin import CheckSMRFOutputs


class TestLakes(CheckSMRFOutputs, SMRFTestCaseLakes):
    """
    Integration test for SMRF without threading.
        - serial simulation
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.smrf = run_smrf(cls.run_config)


class TestLakesThreaded(TestLakes):
    """
    Integration test for SMRF.
        - Threading variables
        - HRRR files read first
    """

    @classmethod
    def configure(cls):
        cls.run_config = cls.thread_config()


class TestLakesHRRRTimestep(TestLakes):
    """
    Integration test for SMRF.
        - Serial variables
        - Load HRRR at each timestep
    """

    @classmethod
    def configure(cls):

        config = cls.base_config_copy()
        config.raw_cfg['gridded']['hrrr_load_method'] = 'timestep'

        config.apply_recipes()
        cls.run_config = cast_all_variables(config, config.mcfg)


class TestLakesThreadedHRRR(TestLakes):
    """
    Integration test for SMRF.
        - Threading variables
        - Load HRRR at each timestep
    """

    @classmethod
    def configure(cls):

        config = cls.base_config_copy()
        config.raw_cfg['system'].update(cls.THREAD_CONFIG)

        config.raw_cfg['gridded']['hrrr_load_method'] = 'timestep'

        config.apply_recipes()
        cls.run_config = cast_all_variables(config, config.mcfg)
