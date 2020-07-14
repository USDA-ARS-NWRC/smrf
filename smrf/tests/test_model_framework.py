import pytz
from pandas import to_datetime

from smrf.framework.model_framework import SMRF
from smrf.tests.smrf_test_case import SMRFTestCase


class TestModelFramework(SMRFTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.smrf = SMRF(cls.config_file)

    def test_start_date(self):
        self.assertEqual(
            self.smrf.start_date,
            to_datetime(self.smrf.config['time']['start_date'], utc=True)
        )

    def test_end_date(self):
        self.assertEqual(
            self.smrf.end_date,
            to_datetime(self.smrf.config['time']['end_date'], utc=True)
        )

    def test_time_zone(self):
        self.assertEqual(self.smrf.time_zone, pytz.UTC)

    def test_date_time(self):
        self.assertEqual(
            self.smrf.date_time[0],
            to_datetime('1998-01-14 15:00:00', utc=True)
        )
        self.assertEqual(
            self.smrf.date_time[-1],
            to_datetime('1998-01-14 19:00:00', utc=True)
        )
        self.assertEqual(
            self.smrf.date_time[0].tzname(),
            str(pytz.UTC)
        )
        self.assertEqual(
            type(self.smrf.date_time),
            list
        )

    def test_assert_time_steps(self):
        self.assertEqual(self.smrf.time_steps, 5)


class TestModelFrameworkMST(SMRFTestCase):
    """
    Test timezone handling for MST.
    """
    TIMEZONE = pytz.timezone('MST')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        base_config = cls.base_config_copy()
        base_config.cfg['time']['time_zone'] = 'MST'
        cls.smrf = SMRF(base_config)

    def test_timezone_error(self):
        base_config = self.base_config
        base_config.cfg['time']['time_zone'] = 'mst'
        with self.assertRaises(Exception):
            SMRF(base_config)

    def test_start_date(self):
        self.assertEqual(
            self.smrf.start_date,
            to_datetime(self.smrf.config['time']['start_date']).tz_localize(
                self.TIMEZONE
            )
        )

    def test_end_date(self):
        self.assertEqual(
            self.smrf.end_date,
            to_datetime(self.smrf.config['time']['end_date']).tz_localize(
                self.TIMEZONE
            )
        )

    def test_time_zone(self):
        self.assertEqual(self.smrf.time_zone, self.TIMEZONE)

    def test_date_time(self):
        self.assertEqual(
            self.smrf.date_time[0],
            to_datetime('1998-01-14 15:00:00').tz_localize(self.TIMEZONE)
        )
        self.assertEqual(
            self.smrf.date_time[-1],
            to_datetime('1998-01-14 19:00:00').tz_localize(self.TIMEZONE)
        )
        self.assertEqual(
            self.smrf.date_time[0].tz.zone,
            self.TIMEZONE.zone
        )
