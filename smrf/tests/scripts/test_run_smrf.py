import unittest
from io import StringIO
from unittest.mock import patch

from .script_test_helper import load_script_as_module

script = load_script_as_module('run_smrf')


class TestRunSmrf(unittest.TestCase):
    def setUp(self):
        self.argument_parser = script.argument_parser()

    @patch('sys.stderr', new=StringIO())
    def test_requires_config_file(self):
        with self.assertRaises(SystemExit):
            self.argument_parser.parse_args([])


if __name__ == '__main__':
    unittest.main()
