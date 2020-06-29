#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestLakes(SMRFTestCaseLakes):
    """
    Integration test for SMRF using reynolds mountain east without threading
    """
    @classmethod
    def setUpClass(cls):
        """
        Runs the short simulation over reynolds mountain east
        """
        super().setUpClass()

        run_smrf(cls.config_file)

    def tearDown(self):
        pass

    def test_air_temp(self):
        """Test Lakes air_temp"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'air_temp.nc'),
            os.path.join(self.output, 'air_temp.nc')
        )

    def test_precip_temp(self):
        """Test Lakes precip_temp"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'precip_temp.nc'),
            os.path.join(self.output, 'precip_temp.nc')
        )

    def test_net_solar(self):
        """Test Lakes net_solar"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'net_solar.nc'),
            os.path.join(self.output, 'net_solar.nc')
        )

    def test_percent_snow(self):
        """Test Lakes percent_snow"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'percent_snow.nc'),
            os.path.join(self.output, 'percent_snow.nc')
        )

    def test_precip(self):
        """Test Lakes precip"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'precip.nc'),
            os.path.join(self.output, 'precip.nc')
        )

    def test_thermal(self):
        """Test Lakes thermal"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'thermal.nc'),
            os.path.join(self.output, 'thermal.nc')
        )

    def test_wind_speed(self):
        """Test Lakes wind_speed"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'wind_speed.nc'),
            os.path.join(self.output, 'wind_speed.nc')
        )

    def test_wind_direction(self):
        """Test Lakes wind_direction"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'wind_direction.nc'),
            os.path.join(self.output, 'wind_direction.nc')
        )

    def test_snow_density(self):
        """Test Lakes snow_density"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'snow_density.nc'),
            os.path.join(self.output, 'snow_density.nc')
        )

    def test_vapor_pressure(self):
        """Test Lakes vapor_pressure"""

        self.compare_netcdf_files(
            os.path.join(self.gold, 'vapor_pressure.nc'),
            os.path.join(self.output, 'vapor_pressure.nc')
        )
