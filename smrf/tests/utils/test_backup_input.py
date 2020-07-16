import os

from smrf import __version__
from smrf.framework.model_framework import SMRF
from smrf.tests.smrf_test_case import SMRFTestCase
from smrf.utils.utils import backup_input


class TestBackupInput(SMRFTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.smrf = SMRF(cls.config_file)
        cls.smrf.loadTopo()
        cls.smrf.create_distribution()
        cls.smrf.loadData()

    def test_backup_version(self):

        backup_input(self.smrf.data, self.base_config)

        backup_config = os.path.join(
            self.base_config.cfg['output']['out_location'],
            'input_backup',
            'backup_config.ini')

        with open(backup_config) as f:
            lines = f.readlines()
            self.assertTrue(__version__ in lines[1])
