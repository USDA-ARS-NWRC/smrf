"""
Created on March 14, 2017
Originally written by Scott Havens in 2015
@author: Micah Johnson

**Creating Custom NASDE Models**
--------------------------------
    When creating a new NASDE model make sure you adhere to the following:

    1. Add a new class to the nasde_models
        For example see :func:`~smrf.envphys.nasde_models.Susong1999`.

    #. Add the new model to the MODEL map in Snow :func:`~smrf.envphys.snow`

    #. Create a custom distribution function with a unique in
       :func:`~smrf.distribute.precipitation.distribute` to create the
       structure for the new model. For an example see
       :func:`~smrf.distribute.precipitation.distribute_for_susong1999`.

    #. Update documentation and run smrf!

"""

import numpy as np
from smrf.envphys.nasde_model import Marks2017, PiecewiseSusong1999, Susong1999
from types import MappingProxyType


class Snow:
    MODELS = MappingProxyType({
        "susong1999": Susong1999,
        "piecewise_susong1999": PiecewiseSusong1999,
        "marks2017": Marks2017,
    })

    @staticmethod
    def phase_and_density(temperature, precipitation, nasde_model):
        """
        Uses various new accumulated snow density models to estimate the snow
        density of precipitation that falls during sub-zero conditions.
        The models all are based on the dew point temperature and the amount of
        precipitation, All models used here must return a dictionary containing
        the keywords pcs and rho_s for percent snow and snow density
        respectively.

        Args:
            temperature: a single timestep of the distributed dew point
              temperature
            precipitation: a numpy array of the distributed precipitation
            nasde_model: string value set in the configuration file
              representing the method for estimating density of new snow that
              has just fallen.

        Returns:
            tuple:
            Returns a tuple containing the snow density field and the percent
            snow as determined by the NASDE model.

            - **snow_density** (*numpy.array*) - Snow density values in kg/m^3
            - **percent_snow** (*numpy.array*) -  Percent of the precipitation
                that is snow in values 0.0-1.0.

        """

        precipitation = np.array(precipitation)
        temperature = np.array(temperature)

        if nasde_model not in Snow.MODELS:
            raise ValueError(
                "{0} is not an implemented new accumulated snow density "
                "(NASDE) model! Check the config file under "
                "precipitation""".format(nasde_model))

        result = Snow.MODELS.get(nasde_model).run(temperature, precipitation)
        return result['rho_s'], result['pcs']
