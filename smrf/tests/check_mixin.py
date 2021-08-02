import numpy as np


class CheckSMRFOutputs(object):
    """Check the SMRF test case for all the variables. To be used as a
    mixin for tests to avoid these tests running more than once.

    Example:
        TestSomethingNew(CheckSMRFOutputs, SMRFTestCase)
    """

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


class CheckSMRFOutputRatios(object):
    """Check the SMRF test case for all the variables. To be used as a
    mixin for tests to avoid these tests running more than once.

    Example:
        TestSomethingNew(CheckSMRFOutputRatios, SMRFTestCase)
            RATIO_MAP = {
                'air_temp': 1.0,
                'precip': 2.0,
            }
    """
    RATIO_MAP = {}

    def _assert_ratio(self, file_name, variable):
        # default ratio is 1:1
        desired_ratio = self.RATIO_MAP.get(variable, 1.0)
        ratio, ignore_index = self.evaluate_netcdf_ratio(file_name)
        # make sure we have some data
        assert not np.all(ignore_index)
        # assert that the data is all equal to the expected ratio
        assert np.all(ratio[~ignore_index] == desired_ratio)

    def test_air_temp(self):
        self._assert_ratio('air_temp.nc', 'air_temp')

    def test_precip_temp(self):
        self._assert_ratio('precip_temp.nc', 'precip_temp')

    def test_net_solar(self):
        self._assert_ratio('net_solar.nc', 'net_solar')

    def test_percent_snow(self):
        self._assert_ratio('percent_snow.nc', 'percent_snow')

    def test_precip(self):
        self._assert_ratio('precip.nc', 'precip')

    def test_thermal(self):
        self._assert_ratio('thermal.nc', 'thermal')

    def test_wind_speed(self):
        self._assert_ratio('wind_speed.nc', 'wind_speed')

    def test_wind_direction(self):
        self._assert_ratio('wind_direction.nc', 'wind_direction')

    def test_snow_density(self):
        self._assert_ratio('snow_density.nc', 'snow_density')

    def test_vapor_pressure(self):
        self._assert_ratio('vapor_pressure.nc', 'vapor_pressure')
