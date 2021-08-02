
class Modifiers:
    INPUT_SCALAR_KEY = "input_scalar_factor"
    OUTPUT_SCALAR_KEY = "output_scalar_factor"
    KEY_OPTIONS = [INPUT_SCALAR_KEY, OUTPUT_SCALAR_KEY]

    def __init__(self, input_scalar, output_scalar):
        self._input_scalar = input_scalar
        self._output_scalar = output_scalar

    @classmethod
    def from_variable_config(cls, cfg):
        input_scalar = cls._scalar_value_from_scalar_type_key(
            "input_scalar_type", cfg)
        output_scalar = cls._scalar_value_from_scalar_type_key(
            "output_scalar_type", cfg)
        return cls(input_scalar, output_scalar)

    @classmethod
    def _scalar_value_from_scalar_type_key(cls, type_key, cfg):
        input_scalar_type = cfg.get(type_key)
        if input_scalar_type is None:
            return None
        scalar_key = f"{type_key.split('_type')[0]}_{input_scalar_type}"
        cls._validate_scalar_key(scalar_key)
        return cfg[scalar_key]

    @classmethod
    def _validate_scalar_key(cls, key):
        if key not in cls.KEY_OPTIONS:
            raise ValueError(f"{key} is not a valid key option. Valid options:"
                             f" {cls.KEY_OPTIONS}")

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
