from unittest.mock import patch
from inicheck.tools import cast_all_variables
import numpy as np
from parameterized import parameterized

from smrf.tests.mock_helpers import SmrfMocks
from smrf.tests.smrf_test_case import SMRFTestCase
import smrf


class ConfigPermutations:
    def __init__(self, config_changes, distribute_section, variable,
                 expected_array):
        self.config_changes = config_changes
        self.distribute_section = distribute_section
        self.variable = variable
        self.expected_array = expected_array


class TestDistributePermutations(SMRFTestCase):

    @classmethod
    def static_config_changes(cls):
        config = cls.base_config_copy()
        config.raw_cfg['system']['threading'] = False
        config.raw_cfg['time']['start_date'] = '1998-01-14 16:00'
        config.raw_cfg['time']['end_date'] = '1998-01-14 17:00'

        return config

    @classmethod
    def configure_permutation(cls, permutation):
        config = cls.static_config_changes()
        config.raw_cfg['system']['threading'] = False
        for k, v in permutation.items():
            config.raw_cfg[k].update(v)

        config.apply_recipes()
        run_config = cast_all_variables(config, config.mcfg)
        return run_config

    @patch('smrf.framework.SMRF.loadTopo', new=SmrfMocks.mock_load_topo)
    def _prep_smrf_mock_topo(self, cfg):
        s = smrf.framework.SMRF(cfg)
        s.loadTopo()
        s.create_distribution()
        s.loadData()
        s.initialize_distribution()
        return s

    @parameterized.expand([
        (ConfigPermutations(
            config_changes={"precip": {
                "input_scalar_type": "factor",
                "input_scalar_factor": 1.0,
                "output_scalar_type": "factor",
                "output_scalar_factor": 2.0
            }},
            distribute_section="precipitation",
            variable="precip",
            expected_array=np.array(
                [[8.0454048, 7.9379243, 7.615483, 7.8304439],
                 [8.0454048, 7.7767037, 7.8841841, 7.9379243],
                 [8.0454048, 7.9379243, 7.9379243, 8.1528852],
                 [7.8304439, 7.7767037, 8.0454048, 8.099145]
                 ])),),
    ])
    def test_permutations_precip(self, test_permutation):
        cfg = self.configure_permutation(test_permutation.config_changes)
        s = self._prep_smrf_mock_topo(cfg)
        # only running one timestep
        t = s.date_time[0]
        # 1. Air temperature
        s.distribute['air_temp'].distribute(s.data.air_temp.loc[t])
        # 2. Vapor pressure
        s.distribute['vapor_pressure'].distribute(
            s.data.vapor_pressure.loc[t],
            s.distribute['air_temp'].air_temp)

        # 4. Precipitation
        s.distribute['precipitation'].distribute(
            s.data.precip.loc[t],
            s.distribute['vapor_pressure'].dew_point,
            s.distribute['vapor_pressure'].precip_temp,
            s.distribute['air_temp'].air_temp,
            t,
            s.data.wind_speed.loc[t],
            s.data.air_temp.loc[t])

        result = getattr(
            s.distribute[test_permutation.distribute_section],
            test_permutation.variable
        )
        np.testing.assert_almost_equal(test_permutation.expected_array, result)
