import unittest
from io import StringIO
from unittest.mock import patch

from .script_test_helper import load_script_as_module

script = load_script_as_module('gen_maxus')


class TestGenMaxusArguments(unittest.TestCase):
    def setUp(self):
        self.argument_parser = script.argument_parser()

    @patch('sys.stderr', new=StringIO())
    def test_require_dem(self):
        with self.assertRaises(SystemExit):
            self.argument_parser.parse_args([])

    def test_only_requires_dem(self):
        self.argument_parser.parse_args(['dem'])

    def test_output_file_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual('./maxus.nc', args.out_maxus)

        args = self.argument_parser.parse_args(['dem', '--out_maxus', 'file'])
        self.assertEqual('file', args.out_maxus)

        args = self.argument_parser.parse_args(['dem', '-O', 'file2'])
        self.assertEqual('file2', args.out_maxus)

    def test_increment_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual(5, args.increment)

        args = self.argument_parser.parse_args(['dem', '--increment', '1'])
        self.assertEqual(1, args.increment)

        args = self.argument_parser.parse_args(['dem', '-i', '2'])
        self.assertEqual(2, args.increment)

    def test_sv_global_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual(500, args.sv_global)

        args = self.argument_parser.parse_args(['dem', '--sv_global', '10'])
        self.assertEqual(10, args.sv_global)

        args = self.argument_parser.parse_args(['dem', '-dmax', '20'])
        self.assertEqual(20, args.sv_global)

    def test_sv_local_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual(100, args.sv_local)

        args = self.argument_parser.parse_args(['dem', '--sv_local', '10'])
        self.assertEqual(10, args.sv_local)

        args = self.argument_parser.parse_args(['dem', '-l', '20'])
        self.assertEqual(20, args.sv_local)

    def test_height_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual(3, args.height)

        args = self.argument_parser.parse_args(['dem', '--height', '5'])
        self.assertEqual(5, args.height)

        args = self.argument_parser.parse_args(['dem', '-H', '10'])
        self.assertEqual(10, args.height)

    def test_window_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual(100, args.window)

        args = self.argument_parser.parse_args(['dem', '--window', '30'])
        self.assertEqual(30, args.window)

        args = self.argument_parser.parse_args(['dem', '-W', '50'])
        self.assertEqual(50, args.window)

    def test_var_name_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual('dem', args.var_name)

        args = self.argument_parser.parse_args(['dem', '--var_name', 'name'])
        self.assertEqual('name', args.var_name)

        args = self.argument_parser.parse_args(['dem', '-N', 'name2'])
        self.assertEqual('name2', args.var_name)

    def test_make_tbreak_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual(False, args.make_tbreak)

        args = self.argument_parser.parse_args(
            ['dem', '--make_tbreak', 'true'])
        self.assertEqual(True, args.make_tbreak)

        args = self.argument_parser.parse_args(['dem', '-tb', '1'])
        self.assertEqual(True, args.make_tbreak)

    def test_out_tbreak_argument(self):
        args = self.argument_parser.parse_args(['dem'])
        self.assertEqual('./tbreak.nc', args.out_tbreak)

        args = self.argument_parser.parse_args(['dem', '--out_tbreak', 'file'])
        self.assertEqual('file', args.out_tbreak)

        args = self.argument_parser.parse_args(['dem', '-OTB', 'file2'])
        self.assertEqual('file2', args.out_tbreak)


if __name__ == '__main__':
    unittest.main()
