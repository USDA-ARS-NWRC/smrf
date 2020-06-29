#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_full_smrf
----------------------------------

Tests for an entire smrf run. The SMRF integration run!
"""

import shutil
import unittest
from copy import copy
from os.path import abspath, isdir, join

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestThreadedRME(SMRFTestCase):
    """
    Integration test for SMRF using reynolds mountain east
    """
    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """
        super().setUpClass()

        cls.gold = abspath(join(cls.test_dir, 'RME', 'gold'))
        cls.output = join(cls.test_dir, 'RME', 'output')

        # Remove any potential files to ensure fresh run
        if isdir(cls.output):
            shutil.rmtree(cls.output)

        run_smrf(cls.config_file)

    def test_air_temp(self):
        """Test RME threaded air_temp"""

        self.compare_netcdf_files(
            join(self.gold, 'air_temp.nc'),
            join(self.output, 'air_temp.nc')
        )

    def test_precip_temp(self):
        """Test RME threaded precip_temp"""

        self.compare_netcdf_files(
            join(self.gold, 'precip_temp.nc'),
            join(self.output, 'precip_temp.nc')
        )

    def test_net_solar(self):
        """Test RME threaded net_solar"""

        self.compare_netcdf_files(
            join(self.gold, 'net_solar.nc'),
            join(self.output, 'net_solar.nc')
        )

    def test_percent_snow(self):
        """Test RME threaded percent_snow"""

        self.compare_netcdf_files(
            join(self.gold, 'percent_snow.nc'),
            join(self.output, 'percent_snow.nc')
        )

    def test_precip(self):
        """Test RME threaded precip"""

        self.compare_netcdf_files(
            join(self.gold, 'precip.nc'),
            join(self.output, 'precip.nc')
        )

    def test_thermal(self):
        """Test RME threaded thermal"""

        self.compare_netcdf_files(
            join(self.gold, 'thermal.nc'),
            join(self.output, 'thermal.nc')
        )

    def test_wind_speed(self):
        """Test RME threaded wind_speed"""

        self.compare_netcdf_files(
            join(self.gold, 'wind_speed.nc'),
            join(self.output, 'wind_speed.nc')
        )

    def test_wind_direction(self):
        """Test RME threaded wind_direction"""

        self.compare_netcdf_files(
            join(self.gold, 'wind_direction.nc'),
            join(self.output, 'wind_direction.nc')
        )

    def test_snow_density(self):
        """Test RME threaded snow_density"""

        self.compare_netcdf_files(
            join(self.gold, 'snow_density.nc'),
            join(self.output, 'snow_density.nc')
        )

    def test_vapor_pressure(self):
        """Test RME threaded vapor_pressure"""

        self.compare_netcdf_files(
            join(self.gold, 'vapor_pressure.nc'),
            join(self.output, 'vapor_pressure.nc')
        )


class TestRME(SMRFTestCase):
    """
    Integration test for SMRF using reynolds mountain east without threading
    """
    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """
        super().setUpClass()

        cls.gold = abspath(join(cls.test_dir, 'RME', 'gold'))
        cls.output = join(cls.test_dir, 'RME', 'output')

        # Remove any potential files to ensure fresh run
        if isdir(cls.output):
            shutil.rmtree(cls.output)

        config = copy(cls.base_config)
        config.raw_cfg['system']['threading'] = False

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        run_smrf(config)

    def test_air_temp(self):
        """Test RME air_temp"""

        self.compare_netcdf_files(
            join(self.gold, 'air_temp.nc'),
            join(self.output, 'air_temp.nc')
        )

    def test_precip_temp(self):
        """Test RME precip_temp"""

        self.compare_netcdf_files(
            join(self.gold, 'precip_temp.nc'),
            join(self.output, 'precip_temp.nc')
        )

    def test_net_solar(self):
        """Test RME net_solar"""

        self.compare_netcdf_files(
            join(self.gold, 'net_solar.nc'),
            join(self.output, 'net_solar.nc')
        )

    def test_percent_snow(self):
        """Test RME percent_snow"""

        self.compare_netcdf_files(
            join(self.gold, 'percent_snow.nc'),
            join(self.output, 'percent_snow.nc')
        )

    def test_precip(self):
        """Test RME precip"""

        self.compare_netcdf_files(
            join(self.gold, 'precip.nc'),
            join(self.output, 'precip.nc')
        )

    def test_thermal(self):
        """Test RME thermal"""

        self.compare_netcdf_files(
            join(self.gold, 'thermal.nc'),
            join(self.output, 'thermal.nc')
        )

    def test_wind_speed(self):
        """Test RME wind_speed"""

        self.compare_netcdf_files(
            join(self.gold, 'wind_speed.nc'),
            join(self.output, 'wind_speed.nc')
        )

    def test_wind_direction(self):
        """Test RME wind_direction"""

        self.compare_netcdf_files(
            join(self.gold, 'wind_direction.nc'),
            join(self.output, 'wind_direction.nc')
        )

    def test_snow_density(self):
        """Test RME snow_density"""

        self.compare_netcdf_files(
            join(self.gold, 'snow_density.nc'),
            join(self.output, 'snow_density.nc')
        )

    def test_vapor_pressure(self):
        """Test RME vapor_pressure"""

        self.compare_netcdf_files(
            join(self.gold, 'vapor_pressure.nc'),
            join(self.output, 'vapor_pressure.nc')
        )


if __name__ == '__main__':
    unittest.main()
