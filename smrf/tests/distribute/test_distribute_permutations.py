from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes
from smrf.tests.check_mixin import CheckSMRFOutputRatios


class TestDistributePermutations(CheckSMRFOutputRatios, SMRFTestCaseLakes):
    RATIO_MAP = {
        'precip': 2.0
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cfg = cls.configure_permutation({"precip": {
            "input_scalar_type": "factor",
            "input_scalar_factor": 1.0,
            "output_scalar_type": "factor",
            "output_scalar_factor": 2.0
        }})

        run_smrf(cfg)

    @classmethod
    def configure_permutation(cls, permutation):
        config = cls.base_config_copy()
        config.raw_cfg['system']['threading'] = False
        for k, v in permutation.items():
            config.raw_cfg[k].update(v)

        config.apply_recipes()
        run_config = cast_all_variables(config, config.mcfg)
        return run_config
