
class Modifiers:
    """
    The Modifiers class allows for configurable modifications to input data
    and post-distribution data to account for known biases. This default
    implementation can multiply the input and output data by a scaling factor.
    """
    INPUT_SCALAR_TYPE_KEY = "input_scalar_type"
    INPUT_SCALAR_KEY = "input_scalar_factor"
    OUTPUT_SCALAR_TYPE_KEY = "output_scalar_type"
    OUTPUT_SCALAR_KEY = "output_scalar_factor"
    SCALAR_KEY_OPTIONS = [INPUT_SCALAR_KEY, OUTPUT_SCALAR_KEY]

    def __init__(self, input_scalar, output_scalar):
        """

        Args:
            input_scalar: float value for scaling the input data
            output_scalar: float value for scaling the output data
        """
        self._input_scalar = input_scalar
        self._output_scalar = output_scalar

    @classmethod
    def from_variable_config(cls, cfg):
        """
        Instantiate the Modifiers class from the variable config section

        Args:
            cfg: dictionary of config values

        Returns:
            Modifiers instance
        """
        input_scalar = cls._scalar_value_from_scalar_type_key(
            cls.INPUT_SCALAR_TYPE_KEY, cfg)
        output_scalar = cls._scalar_value_from_scalar_type_key(
            cls.OUTPUT_SCALAR_TYPE_KEY, cfg)
        return cls(input_scalar, output_scalar)

    @classmethod
    def _scalar_value_from_scalar_type_key(cls, type_key, cfg):
        """
        Flexible approach to finding the key holding the scalar value given
        the key specifying the type of scaling

        Args:
            type_key: the config key corresponding to the type of scaling
            cfg: dictionary of config values
        Returns:
            the scalar value
        """
        input_scalar_type = cfg.get(type_key)
        if input_scalar_type is None:
            return None
        scalar_key = f"{type_key.split('_type')[0]}_{input_scalar_type}"
        cls._validate_scalar_key(scalar_key)
        return cfg[scalar_key]

    @classmethod
    def _validate_scalar_key(cls, key):
        """
        Validate that the scalar key is allowed

        Args:
            key: the scalar config key
        """
        if key not in cls.SCALAR_KEY_OPTIONS:
            raise ValueError(f"{key} is not a valid key option. Valid options:"
                             f" {cls.SCALAR_KEY_OPTIONS}")

    @staticmethod
    def _scale_data(data, modification):
        if modification is None:
            return data
        else:
            return modification * data

    def scale_input_data(self, data):
        return self._scale_data(data, self._input_scalar)

    def scale_output_data(self, data):
        return self._scale_data(data, self._output_scalar)
