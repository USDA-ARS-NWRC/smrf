from inicheck.tools import cast_all_variables


class BaseRecipes():
    """Test the recipes
    """

    def cast_recipes(self, config):
        """Cast the inicheck recipes
        Arguments:
            config {UserConfig} -- UserConfig object to modify
        Returns:
            UserConfig -- Modified UserConfig object
        """

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        return config

    def master_config(self, config):
        """Create a master config dictionary with a
        list of the keys
        Arguments:
            config {UserConfig} -- UserConfig object to create
                a master config from
        Returns:
            [dict] -- master_config dict that has all sections
                and items from the provided UserConfig
        """

        master_config = {}
        for key in config.mcfg.cfg.keys():
            master_config[key] = list(config.mcfg.cfg[key].keys())

        return master_config

    def check_config(self, config, master_config):
        """Check that the config read by inicheck matches
        the master_config (expected) results
        Arguments:
            config {inicheck UserConfig} -- UserConfig object to check
            master_config {dict} -- dict of sections and items
                that should be in the UserConfig
        """

        # ensure that there are no
        for key, items in master_config.items():
            self.check_config_section(config, master_config, key)

    def check_config_section(self, config, master_config, section):
        """Check that the config read by inicheck matches
        the master_config (expected) results
        Arguments:
            config {inicheck UserConfig} -- UserConfig object to check
            master_config {dict} -- dict of sections and items
                that should be in the UserConfig
        """

        # ensure that there are no
        items = master_config[section]
        test_items = list(config.cfg[section].keys())

        for item in items:
            self.assertTrue(item in test_items)
            test_items.remove(item)

        self.assertTrue(len(test_items) == 0)
