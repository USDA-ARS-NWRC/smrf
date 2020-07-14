from smrf.framework.model_framework import SMRF, run_smrf
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestThreading(SMRFTestCaseLakes):
    THREAD_VARIABLE_COUNT = 36

    @staticmethod
    def get_variables(config):
        s = SMRF(config)
        s.loadTopo()
        s.initializeDistribution()
        s.loadData()

        for v in s.distribute:
            s.distribute[v].initialize(s.topo, s.data)

        s.set_queue_variables()

        return s.thread_queue_variables

    def test_thread_variables(self):
        variables = self.get_variables(self.base_config)
        self.assertEqual(len(variables), self.THREAD_VARIABLE_COUNT)

    def test_multi_thread_variables(self):
        # Try to mimic the testing errors where the Lakes will
        # fail in threading after running the non threaded

        run_smrf(self.base_config)

        config = self.thread_config()

        thread_variables = self.get_variables(config)

        self.assertEqual(len(thread_variables), self.THREAD_VARIABLE_COUNT)
