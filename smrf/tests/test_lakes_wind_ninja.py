#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestLakes(SMRFTestCaseLakes):
    """
    Integration test for SMRF without threading.
    Runs the short simulation over reynolds mountain east.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.smrf = run_smrf(cls.config_file)

    def setUp(self):
        self.assert_thread_variables()

    def test_air_temp(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'air_temp.nc'),
            os.path.join(self.output, 'air_temp.nc')
        )

    def test_precip_temp(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'precip_temp.nc'),
            os.path.join(self.output, 'precip_temp.nc')
        )

    def test_net_solar(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'net_solar.nc'),
            os.path.join(self.output, 'net_solar.nc')
        )

    def test_percent_snow(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'percent_snow.nc'),
            os.path.join(self.output, 'percent_snow.nc')
        )

    def test_precip(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'precip.nc'),
            os.path.join(self.output, 'precip.nc')
        )

    def test_thermal(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'thermal.nc'),
            os.path.join(self.output, 'thermal.nc')
        )

    def test_wind_speed(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'wind_speed.nc'),
            os.path.join(self.output, 'wind_speed.nc')
        )

    def test_wind_direction(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'wind_direction.nc'),
            os.path.join(self.output, 'wind_direction.nc')
        )

    def test_snow_density(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'snow_density.nc'),
            os.path.join(self.output, 'snow_density.nc')
        )

    def test_vapor_pressure(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'vapor_pressure.nc'),
            os.path.join(self.output, 'vapor_pressure.nc')
        )


class TestLakesThreaded(SMRFTestCaseLakes):
    """
    Integration test for SMRF.
    Runs the short simulation over reynolds mountain east.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        config = cls.base_config_copy()
        config.raw_cfg['system'].update({
            'threading': True,
            'max_queue': 1,
            'time_out': 5
        })

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        cls.smrf = run_smrf(config)

    def tearDown(self):
        pass

    def setUp(self):
        self.assert_thread_variables()

    def test_air_temp(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'air_temp.nc'),
            os.path.join(self.output, 'air_temp.nc')
        )

    def test_precip_temp(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'precip_temp.nc'),
            os.path.join(self.output, 'precip_temp.nc')
        )

    def test_net_solar(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'net_solar.nc'),
            os.path.join(self.output, 'net_solar.nc')
        )

    def test_percent_snow(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'percent_snow.nc'),
            os.path.join(self.output, 'percent_snow.nc')
        )

    def test_precip(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'precip.nc'),
            os.path.join(self.output, 'precip.nc')
        )

    def test_thermal(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'thermal.nc'),
            os.path.join(self.output, 'thermal.nc')
        )

    def test_wind_speed(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'wind_speed.nc'),
            os.path.join(self.output, 'wind_speed.nc')
        )

    def test_wind_direction(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'wind_direction.nc'),
            os.path.join(self.output, 'wind_direction.nc')
        )

    def test_snow_density(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'snow_density.nc'),
            os.path.join(self.output, 'snow_density.nc')
        )

    def test_vapor_pressure(self):
        self.compare_netcdf_files(
            os.path.join(self.gold, 'vapor_pressure.nc'),
            os.path.join(self.output, 'vapor_pressure.nc')
        )
