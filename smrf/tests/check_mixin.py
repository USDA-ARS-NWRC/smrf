
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
