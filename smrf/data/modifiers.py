def get_scalar_value_key(config, stage):
    """
    Get the config key that holds the values defining a data scalar approach
    Args:
        config: the variable specific config section
        stage: the stage that the scaling is being applied to. Allowed values are ["input", "output"]

    Returns:
        scalar_value_key: the config key that can access the values needed to scale the data
    """
    if stage not in ["input", "output"]:
        raise ValueError(f"{stage} is not an allowed stage value for data scaling")
    method = config.get(f"{stage}_scalar_type")
    if method is None:
        return None
    return f"{stage}_scalar_{method}"


def scale_data(data, scalar_key, config):
    """
    Scale the input vector data based on user config
    Args:
        data: the data to be scaled. This is a pandas series or a numpy array
        scalar_key: config key for style of scaling. This let's us reuse this method for input or output scaling
        config: The variable config dictionary

    Returns:
        scaled_data: The scaled data in the same format as the input
    """
    if scalar_key in ["input_scalar_factor", "output_scalar_factor"]:
        scalar = config[scalar_key]
        scaled_data = data * scalar
    else:
        raise NotImplementedError(f"{scalar_key} is not an implemented scalar method.")

    return scaled_data
