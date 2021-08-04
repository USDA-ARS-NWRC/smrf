from parameterized import parameterized

from smrf.tests.recipes.base_recipe import BaseRecipes
from smrf.tests.smrf_test_case import SMRFTestCase


class TestPrecipRecipes(SMRFTestCase, BaseRecipes):
    SECTION = "precip"

    @parameterized.expand([
        (
            {'input_scalar_type': 'factor', 'input_scalar_factor': 2.0},
            {'input_scalar_type': 'factor', 'input_scalar_factor': 2.0,
             'output_scalar_type': None},
            ['output_scalar_factor']
        ),
        (
            {'output_scalar_type': 'factor', 'output_scalar_factor': 2.0},
            {'output_scalar_type': 'factor', 'output_scalar_factor': 2.0,
             'input_scalar_type': None},
            ['input_scalar_factor']
        ),
        (
            {},
            {'output_scalar_type': None, 'input_scalar_type': None},
            ['input_scalar_factor', 'output_scalar_factor']
        ),
        (
            {'output_scalar_factor': 1.1, 'input_scalar_factor': 2.1},
            {'output_scalar_type': None, 'input_scalar_type': None},
            ['input_scalar_factor', 'output_scalar_factor']
        ),
        (
            {'output_scalar_type': 'None', 'input_scalar_type': 'None',
             'output_scalar_factor': 1.1, 'input_scalar_factor': 2.1},
            {'output_scalar_type': None, 'input_scalar_type': None},
            ['input_scalar_factor', 'output_scalar_factor']
        ),
    ]
    )
    def test_precip_scalar_recipes(self, adj_config, validate_config,
                                   missing_keys):
        config = self.base_config_copy()

        config.raw_cfg['precip'].update(adj_config)
        config = self.cast_recipes(config)

        self.check_config_values(self.SECTION, validate_config, config)
        self.check_keys_not_present(self.SECTION, missing_keys, config)
