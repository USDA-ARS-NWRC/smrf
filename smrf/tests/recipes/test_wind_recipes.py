from smrf.tests.recipes.base_recipe import BaseRecipes
from smrf.tests.smrf_test_case import SMRFTestCase
from smrf.tests.smrf_test_case_lakes import SMRFTestCaseLakes


class TestWindNinjaRecipes(SMRFTestCaseLakes, BaseRecipes):
    """Test the wind ninja recipes
    """

    def test_wind_ninja_recipe(self):
        """Test the wind ninja recipe
        """

        # get the master config list
        master_config = self.master_config(self.base_config)

        # make changes
        master_config['wind'] = [
            'wind_model',
            'wind_ninja_dir',
            'wind_ninja_dxdy',
            'wind_ninja_pref',
            'wind_ninja_tz',
            'wind_ninja_roughness',
            'wind_ninja_height',
            'min',
            'max'
        ]

        self.check_config_section(self.base_config, master_config, 'wind')


class TestWinstralWindRecipes(SMRFTestCase, BaseRecipes):
    """Test the winstral recipes
    """

    def test_winstral_wind_recipe(self):
        """Test the winstral wind recipe
        """

        # get the master config list
        master_config = self.master_config(self.base_config)

        # make changes
        master_config['wind'] = [
            'maxus_netcdf',
            'reduction_factor',
            'wind_model',
            'distribution',
            'detrend',
            'detrend_slope',
            'stations',
            'max',
            'min',
            'idw_power',
            'station_peak',
            'station_default',
            'veg_default',
            'veg_41',
            'veg_42',
            'veg_43',
            'veg_3011',
            'veg_3061'
        ]

        self.check_config_section(self.base_config, master_config, 'wind')


class TestInterpWindRecipes(SMRFTestCase, BaseRecipes):
    """Test the interp recipes
    """

    def test_interp_wind_recipe(self):
        """Test the intper wind recipe
        """
        config = self.base_config_copy()

        adj_config = {
            'wind': {
                'distribution': 'grid',
                'wind_model': 'interp'
            }
        }

        config.raw_cfg.update(adj_config)
        config = self.cast_recipes(config)

        # get the master config list
        master_config = self.master_config(config)

        # make changes
        master_config['wind'] = [
            'wind_model',
            'distribution',
            'detrend',
            'detrend_slope',
            'max',
            'min',
            'grid_mask',
            'grid_method',
            'grid_local'
        ]

        self.check_config_section(config, master_config, 'wind')
