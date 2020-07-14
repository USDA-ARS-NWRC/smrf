import os

from smrf.tests.smrf_test_case import SMRFTestCase


class SMRFTestCaseLakes(SMRFTestCase):
    """
    Runs the short simulation over Lakes.
    """

    basin_dir = SMRFTestCase.test_dir.joinpath('basins', 'Lakes')
    config_file = os.path.join(basin_dir, SMRFTestCase.BASE_INI_FILE_NAME)
    gold_dir = basin_dir.joinpath('gold_hrrr')
