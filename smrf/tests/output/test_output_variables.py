import os
from copy import copy
from glob import glob

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestOutputThreadedVariables(SMRFTestCase):

    def tearDown(self):
        self.remove_output_dir()

    def change_variables(self, new_variables):
        config = copy(self.base_config)
        config.raw_cfg['output'].update({
            'variables': new_variables
        })

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        return config

    def check_outputs(self, new_variables):

        files = glob(os.path.join(
            self.base_config.cfg['output']['out_location'], '*.nc'))
        out_files = [os.path.basename(f).split('.')[0] for f in files]

        out_files.sort()
        new_variables.sort()

        self.assertTrue(new_variables == out_files)

    def test_variables_standard(self):

        new_variables = ['thermal', 'air_temp']
        config = self.change_variables(new_variables)
        run_smrf(config)
        self.check_outputs(new_variables)

    def test_variables_non_standard(self):

        new_variables = ['clear_ir_beam', 'veg_vis_diffuse',
                         'cloud_vis_beam', 'thermal_veg']
        config = self.change_variables(new_variables)
        run_smrf(config)
        self.check_outputs(new_variables)


class TestOutputVariables(TestOutputThreadedVariables):

    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """
        super().setUpClass()

        config = cls.base_config_copy()
        config.raw_cfg['system']['threading'] = False

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)
        cls._base_config = config
