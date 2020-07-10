#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

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

        cls.gold_dir = cls.basin_dir.joinpath('gold')

        run_smrf(cls.config_file)

    def test_air_temp(self):
        self.compare_netcdf_files('air_temp.nc')

    def test_precip_temp(self):
        self.compare_netcdf_files('precip_temp.nc')

    def test_net_solar(self):
        self.compare_netcdf_files('net_solar.nc')

    def test_percent_snow(self):
        self.compare_netcdf_files('percent_snow.nc')

    def test_precip(self):
        self.compare_netcdf_files('precip.nc')

    def test_thermal(self):
        self.compare_netcdf_files('thermal.nc')

    def test_wind_speed(self):
        self.compare_netcdf_files('wind_speed.nc')

    def test_wind_direction(self):
        self.compare_netcdf_files('wind_direction.nc')

    def test_snow_density(self):
        self.compare_netcdf_files('snow_density.nc')

    def test_vapor_pressure(self):
        self.compare_netcdf_files('vapor_pressure.nc')


class TestRME(SMRFTestCase):
    """
    Integration test for SMRF using without threading
    Runs the short simulation over reynolds mountain east
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.gold_dir = cls.basin_dir.joinpath('gold')

        config = cls.base_config_copy()
        config.raw_cfg['system']['threading'] = False

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        run_smrf(config)

    def test_air_temp(self):
        self.compare_netcdf_files('air_temp.nc')

    def test_precip_temp(self):
        self.compare_netcdf_files('precip_temp.nc')

    def test_net_solar(self):
        self.compare_netcdf_files('net_solar.nc')

    def test_percent_snow(self):
        self.compare_netcdf_files('percent_snow.nc')

    def test_precip(self):
        self.compare_netcdf_files('precip.nc')

    def test_thermal(self):
        self.compare_netcdf_files('thermal.nc')

    def test_wind_speed(self):
        self.compare_netcdf_files('wind_speed.nc')

    def test_wind_direction(self):
        self.compare_netcdf_files('wind_direction.nc')

    def test_snow_density(self):
        self.compare_netcdf_files('snow_density.nc')

    def test_vapor_pressure(self):
        self.compare_netcdf_files('vapor_pressure.nc')


if __name__ == '__main__':
    unittest.main()
