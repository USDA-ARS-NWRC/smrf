from .utils import calc_percent_snow, check_temperature


class PiecewiseSusong1999:
    """
    Follows :func:`~smrf.envphys.snow.susong1999` but is the piecewise form
    of table shown there. This model adds to the former by accounting for
    liquid water effect near 0.0 Degrees C.

    The table was estimated by Danny Marks in 2017 which resulted in the
    piecewise equations below:

        Percent Snow:
            .. math::

                \\%_{snow} = \\Bigg \\lbrace{
                    \\frac{-T}{T_{r0}} P_{cr0} + P_{c0}, \\hfill
                    -0.5^{\\circ} C \\leq T \\leq 0.0^{\\circ} C
                     \\atop
                     \\frac{-T_{pp}}{T_{max} + 1.0} P_{c0} + P_{c0},
                     \\hfill 0.0^\\circ C \\leq T \\leq T_{max}
                    }

        Snow Density:
            .. math::
                \\rho_{s} = 50.0 + 1.7 * (T_{pp} + 15.0)^{ex}


                ex = \\Bigg \\lbrace{
                        ex_{min} + \\frac{T_{range} + T_{snow} - T_{max}}
                        {T_{range}} * ex_{r}, \\hfill ex < 1.75
                        \\atop
                        1.75, \\hfill, ex > 1.75
                        }

    """
    EX_MAX = 1.75
    EXR = 0.75
    EX_MIN = 1.0

    TZ = 0.0

    @staticmethod
    def run(tpp, _precipitation, t_max=0.0, t_min=-10.0, check_temps=True):
        """
        Args:
            tpp: A numpy array of temperature, use dew point temperature
                if available [degree C].
            _precipitation: A numpy array of precipitation in millimeters.
                Currently unused.
            t_max: Max temperature that snow density is modeled.
                   Default is 0.0 Degrees C.
            t_min: Minimum temperature that snow density is changing.
                   Default is -10.0 Degrees C.
            check_temps: A boolean value check to apply special temperature
                constraints, this is done using
                :func:`~smrf.envphys.Snow.check_temperature`. Default is True.

        Returns:
            Dictionary:
               - **pcs** (*numpy.array*) - Percent of the precipitation that is
                    snow in values 0.0-1.0.
               - **rho_s** (*numpy.array*) - Density of the fresh snow
                    in kg/m^3.
        """
        # again, this shouldn't be needed in this context
        if check_temps:
            tpp, tsnow = check_temperature(
                tpp, t_max=t_max, t_min=t_min
            )

        pcs = calc_percent_snow(tpp, t_max=t_max)

        # New snow density - no compaction
        t_range = t_max - t_min
        ex = PiecewiseSusong1999.EX_MIN + (
            ((t_range + (tsnow - t_max)) / t_range) * PiecewiseSusong1999.EXR
        )

        ex[ex > PiecewiseSusong1999.EX_MAX] = PiecewiseSusong1999.EX_MAX

        rho_ns = 50.0 + (1.7 * ((tpp - PiecewiseSusong1999.TZ) + 15.0)**ex)

        return {
            'pcs': pcs,
            'rho_s': rho_ns
        }
