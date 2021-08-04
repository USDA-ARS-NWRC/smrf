import netCDF4 as nc
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
    DECIMAL = 4

    def _assert_ratio(self, file_name, variable):
        # default ratio is 1:1
        desired_ratio = self.RATIO_MAP.get(variable, 1.0)
        ratio, ignore_index = self._evaluate_netcdf_ratio(file_name)
        # assert that the data is all equal to the expected ratio
        desired_ratio_array = np.ones_like(ratio) * desired_ratio

        np.testing.assert_almost_equal(
            ratio[~ignore_index],
            desired_ratio_array[~ignore_index],
            decimal=self.DECIMAL
        )

    def _evaluate_netcdf_ratio(self, output_file):
        """
        Find a ratio between the primary variable for 2 datasets.
        Args:
            output_file: path to the test output file

        Returns:
            a tuple of the ratio ndarray and an ndarry of indices that should
            be ignored
        """

        with nc.Dataset(self.gold_dir.joinpath(output_file)) as gold, \
                nc.Dataset(self.output_dir.joinpath(output_file)) as test:

            self._validate_time(gold, test)

            for var_name, v in gold.variables.items():
                if var_name not in self.NON_DISTRIBUTED_VARIABLES:
                    # ratio is meaningless if both cells are zero or nan
                    ignore_indexes = (
                        (test.variables[var_name][:] == 0.0)
                        & (gold.variables[var_name][:] == 0.0)) \
                        | (np.isnan(test.variables[var_name][:])
                           & np.isnan(gold.variables[var_name][:]))
                    return (test.variables[var_name][:] / gold.variables[
                                                              var_name][:],
                            ignore_indexes)

        raise ValueError(f'{output_file} did not return a valid ratio')

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
