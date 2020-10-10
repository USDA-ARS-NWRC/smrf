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

    # Coefficients for snow relationship
    TR0 = 0.5
    PCR0 = 0.25
    PC0 = 0.75

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

    @staticmethod
    def calc_percent_snow(tpp, t_max=0.0):
        """
        Calculates the percent snow for the nasde_models piecewise_susong1999
        and marks2017.

        Args:
            tpp: A numpy array of temperature, use dew point temperature if
                available [degree C].
            t_max: Max temperature that the percent snow is estimated.
                  Default is 0.0 Degrees C.

        Returns:
            numpy.array:
            A fraction of the precipitation at each pixel that is snow provided
            by tpp.
        """

        percent = np.zeros(tpp.shape)

        percent[tpp <= -0.5] = 1.0

        ind = (tpp > -0.5) & (tpp <= 0.0)
        if np.any(ind):
            percent[ind] = (-tpp[ind] / Snow.TR0) * Snow.PCR0 + Snow.PC0

        ind = (tpp > 0.0) & (tpp <= t_max + 1.0)
        if np.any(ind):
            percent[ind] = (-tpp[ind] / (t_max + 1.0)) * Snow.PC0 + Snow.PC0

        return percent

    @staticmethod
    def check_temperature(tpp, t_max=0.0, t_min=-10.0):
        """
        Sets  the precipitation temperature and snow temperature.

        Args:
            tpp: A numpy array of temperature, use dew point temperature
                if available [degrees C].
            t_max: Thresholds the max temperature of the snow [degrees C].
            t_min: Minimum temperature that the precipitation temperature
                [degrees C].

        Returns:
            tuple:
               - **tpp** (*numpy.array*) - Modified precipitation temperature
                         that limited to a minimum set by t_min.
               - **t_snow** (*numpy.array*) - Temperature of the surface of the
                             snow set by the precipitation temperature and
                             limited by t_max, where t_snow > t_max = t_max.

        """

        tpp[tpp < t_min] = t_min

        t_snow = tpp.copy()
        t_snow[tpp > t_max] = t_max

        return tpp, t_snow
