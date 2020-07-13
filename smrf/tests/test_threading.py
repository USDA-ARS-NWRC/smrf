import os
from copy import deepcopy

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import SMRF, run_smrf
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestThreading(SMRFTestCaseLakes):

    def get_variables(self, config):
        s = SMRF(self.base_config)
        s.loadTopo()
        s.initializeDistribution()
        s.loadData()

        for v in s.distribute:
            s.distribute[v].initialize(s.topo, s.data)

        s.set_queue_variables()

        return s.thread_queue_variables

    def test_thread_variables(self):

        variables = self.get_variables(self.base_config)
        self.assertEqual(len(variables), 36)

    def test_multi_thread_variables(self):
        # Try to mimic the testing errors where the Lakes will
        # fail in threading after running the non threaded

        run_smrf(self.base_config)

        config = deepcopy(self.base_config)
        config.raw_cfg['system'].update({
            'threading': True,
            'max_queue': 1,
            'time_out': 2
        })

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        thread_variables = self.get_variables(config)

        self.assertEqual(len(thread_variables), 36)
