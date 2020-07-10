#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_full_smrf
----------------------------------

Tests for an entire smrf run. The SMRF integration run!
"""

import unittest
from os.path import abspath, join

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestThreadedRME(SMRFTestCase):
    """
    Integration test for SMRF.
    Runs the short simulation over reynolds mountain east.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.gold = abspath(join(cls.test_dir, 'RME', 'gold'))

        run_smrf(cls.config_file)

    def test_air_temp(self):
        self.compare_netcdf_files(
            join(self.gold, 'air_temp.nc'),
            join(self.output_dir, 'air_temp.nc')
        )

    def test_precip_temp(self):
        self.compare_netcdf_files(
            join(self.gold, 'precip_temp.nc'),
            join(self.output_dir, 'precip_temp.nc')
        )

    def test_net_solar(self):
        self.compare_netcdf_files(
            join(self.gold, 'net_solar.nc'),
            join(self.output_dir, 'net_solar.nc')
        )

    def test_percent_snow(self):
        self.compare_netcdf_files(
            join(self.gold, 'percent_snow.nc'),
            join(self.output_dir, 'percent_snow.nc')
        )

    def test_precip(self):
        self.compare_netcdf_files(
            join(self.gold, 'precip.nc'),
            join(self.output_dir, 'precip.nc')
        )

    def test_thermal(self):
        self.compare_netcdf_files(
            join(self.gold, 'thermal.nc'),
            join(self.output_dir, 'thermal.nc')
        )

    def test_wind_speed(self):
        self.compare_netcdf_files(
            join(self.gold, 'wind_speed.nc'),
            join(self.output_dir, 'wind_speed.nc')
        )

    def test_wind_direction(self):
        self.compare_netcdf_files(
            join(self.gold, 'wind_direction.nc'),
            join(self.output_dir, 'wind_direction.nc')
        )

    def test_snow_density(self):
        self.compare_netcdf_files(
            join(self.gold, 'snow_density.nc'),
            join(self.output_dir, 'snow_density.nc')
        )

    def test_vapor_pressure(self):
        self.compare_netcdf_files(
            join(self.gold, 'vapor_pressure.nc'),
            join(self.output_dir, 'vapor_pressure.nc')
        )


class TestRME(SMRFTestCase):
    """
    Integration test for SMRF using without threading
    Runs the short simulation over reynolds mountain east
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.gold = abspath(join(cls.test_dir, 'RME', 'gold'))

        config = cls.base_config_copy()
        config.raw_cfg['system']['threading'] = False

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        run_smrf(config)

    def test_air_temp(self):
        self.compare_netcdf_files(
            join(self.gold, 'air_temp.nc'),
            join(self.output_dir, 'air_temp.nc')
        )

    def test_precip_temp(self):
        self.compare_netcdf_files(
            join(self.gold, 'precip_temp.nc'),
            join(self.output_dir, 'precip_temp.nc')
        )

    def test_net_solar(self):
        self.compare_netcdf_files(
            join(self.gold, 'net_solar.nc'),
            join(self.output_dir, 'net_solar.nc')
        )

    def test_percent_snow(self):
        self.compare_netcdf_files(
            join(self.gold, 'percent_snow.nc'),
            join(self.output_dir, 'percent_snow.nc')
        )

    def test_precip(self):
        self.compare_netcdf_files(
            join(self.gold, 'precip.nc'),
            join(self.output_dir, 'precip.nc')
        )

    def test_thermal(self):
        self.compare_netcdf_files(
            join(self.gold, 'thermal.nc'),
            join(self.output_dir, 'thermal.nc')
        )

    def test_wind_speed(self):
        self.compare_netcdf_files(
            join(self.gold, 'wind_speed.nc'),
            join(self.output_dir, 'wind_speed.nc')
        )

    def test_wind_direction(self):
        self.compare_netcdf_files(
            join(self.gold, 'wind_direction.nc'),
            join(self.output_dir, 'wind_direction.nc')
        )

    def test_snow_density(self):
        self.compare_netcdf_files(
            join(self.gold, 'snow_density.nc'),
            join(self.output_dir, 'snow_density.nc')
        )

    def test_vapor_pressure(self):
        self.compare_netcdf_files(
            join(self.gold, 'vapor_pressure.nc'),
            join(self.output_dir, 'vapor_pressure.nc')
        )


if __name__ == '__main__':
    unittest.main()
