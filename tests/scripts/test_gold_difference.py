import unittest
from io import StringIO
from unittest.mock import patch
from argparse import ArgumentError

from .script_test_helper import load_script_as_module

script = load_script_as_module('gold_difference')


class TestGoldDifferenceArguments(unittest.TestCase):
    def setUp(self):
        self.argument_parser = script.argument_parser()

    def test_basin_argument(self):
        args = self.argument_parser.parse_args(['--basin', 'RME'])
        self.assertEqual('RME', args.basin)

        args = self.argument_parser.parse_args(['-b', 'RME'])
        self.assertEqual('RME', args.basin)

        args = self.argument_parser.parse_args(['--basin', 'Lakes'])
        self.assertEqual('Lakes', args.basin)

        with self.assertRaises(SystemExit):
            args = self.argument_parser.parse_args(['--basin', 'ABCDE'])

    def test_gold_dir_argument(self):
        args = self.argument_parser.parse_args(['--gold_dir', 'gold'])
        self.assertEqual('gold', args.gold_dir)

        args = self.argument_parser.parse_args(['-g', 'gold'])
        self.assertEqual('gold', args.gold_dir)

        args = self.argument_parser.parse_args(['--gold_dir', 'gold_hrrr'])
        self.assertEqual('gold_hrrr', args.gold_dir)

        with self.assertRaises(SystemExit):
            args = self.argument_parser.parse_args(['-g', 'ABCDE'])

    def test_old_branch_argument(self):
        args = self.argument_parser.parse_args(['--old_branch', 'master'])
        self.assertEqual('master', args.old_branch)

        args = self.argument_parser.parse_args(['-o', 'gold'])
        self.assertEqual('gold', args.old_branch)

    def test_new_branch_argument(self):
        args = self.argument_parser.parse_args(
            ['--new_branch', 'cool_feature'])
        self.assertEqual('cool_feature', args.new_branch)

        args = self.argument_parser.parse_args(['-n', 'cool_feature'])
        self.assertEqual('cool_feature', args.new_branch)
